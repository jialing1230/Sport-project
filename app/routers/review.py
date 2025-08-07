from flask import Blueprint, request, jsonify, render_template
from datetime import datetime  # ✅ 加這行
from app.database import get_db
from app.models.user_review import UserReview
from app.models.review_template import ReviewTemplate
from app.models.activity import Activity
from app.models.activity_join import ActivityJoin
from app.models.activity_review import ActivityReview  # 新增匯入
from app.models.member import Member
from flask import render_template

review_bp = Blueprint("review", __name__)

@review_bp.route("/reviews/statistics", methods=["GET"])
def get_review_statistics():
    target_member_id = request.args.get("target_member_id")

    # 使用 `with` 語句來正確地進入上下文管理器
    with get_db() as db:
        # 獲取該使用者的所有評論
        reviews = db.query(UserReview).filter(UserReview.target_member_id == target_member_id).all()

        if not reviews:
            return jsonify({
                "total_reviews": 0,
                "average_rating": 0,
                "common_templates": []
            })

        # 計算評論數量和平均評分
        total_reviews = len(reviews)
        average_rating = sum(review.rating for review in reviews) / total_reviews

        # 統計罐頭訊息的出現次數
        template_count = {}
        for review in reviews:
            for template_id in review.template_ids:
                if template_id not in template_count:
                    template_count[template_id] = 0
                template_count[template_id] += 1

        # 找出前三個最常見的罐頭訊息
        sorted_templates = sorted(template_count.items(), key=lambda x: x[1], reverse=True)[:3]
        common_templates = []
        for template_id, count in sorted_templates:
            template = db.query(ReviewTemplate).filter(ReviewTemplate.template_id == template_id).first()
            if template:
                common_templates.append({"template": template.text, "count": count})

        return jsonify({
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "common_templates": common_templates
        })



@review_bp.route("/reviews/last_activity", methods=["GET"])
def get_last_activity():
    target_member_id = request.args.get("target_member_id")
    with get_db() as db:
        # 從 activity_joins 表中查詢該使用者所有參加的活動
        joined_activities = (
            db.query(ActivityJoin, Activity.end_time)
            .join(Activity, ActivityJoin.activity_id == Activity.activity_id)
            .filter(ActivityJoin.member_id == target_member_id, ActivityJoin.status == "joined")
            .all()
        )

        if not joined_activities:
            return jsonify({"last_activity_date": None})

        # 找出結束日期最晚的活動
        latest_activity = max(joined_activities, key=lambda x: x[1])

        return jsonify({"last_activity_date": latest_activity[1].strftime("%Y/%m/%d")})


@review_bp.route("/reviews/organizer_last_activity", methods=["GET"])
def get_organizer_last_activity():
    organizer_id = request.args.get("organizer_id")
    with get_db() as db:
        # 從 activity 表中查詢該使用者作為發起者的所有活動
        organized_activities = (
            db.query(Activity.end_time)
            .filter(Activity.organizer_id == organizer_id)
            .all()
        )

        if not organized_activities:
            return jsonify({"last_activity_date": None})

        # 找出結束日期最晚的活動
        latest_activity_date = max(organized_activities, key=lambda x: x[0])[0]

        return jsonify({"last_activity_date": latest_activity_date.strftime("%Y/%m/%d")})


@review_bp.route("/reviews/organizer_statistics", methods=["GET"])
def get_organizer_statistics():
    organizer_id = request.args.get("organizer_id")

    with get_db() as db:
        # 從 activity 表中查詢該使用者作為發起者的所有活動
        activities = (
            db.query(Activity.activity_id)
            .filter(Activity.organizer_id == organizer_id)
            .all()
        )

        total_activities = len(activities)  # 統計發起活動總數

        if not activities:
            return jsonify({
                "total_reviews": 0,
                "average_rating": 0,
                "common_templates": [],
                "total_activities": 0
            })

        # 提取活動 ID
        activity_ids = [activity.activity_id for activity in activities]

        # 從 activity_reviews 表中查詢所有相關評論
        reviews = (
            db.query(ActivityReview)
            .filter(ActivityReview.activity_id.in_(activity_ids))
            .all()
        )

        if not reviews:
            return jsonify({
                "total_reviews": 0,
                "average_rating": 0,
                "common_templates": [],
                "total_activities": total_activities
            })

        # 計算評論數量和平均星等
        total_reviews = len(reviews)
        average_rating = sum(review.rating for review in reviews) / total_reviews

        # 統計罐頭訊息的出現次數
        template_count = {}
        for review in reviews:
            for template_id in review.template_ids:
                if template_id not in template_count:
                    template_count[template_id] = 0
                template_count[template_id] += 1

        # 找出前三個最常見的罐頭訊息
        sorted_templates = sorted(template_count.items(), key=lambda x: x[1], reverse=True)[:3]
        common_templates = []
        for template_id, count in sorted_templates:
            template = db.query(ReviewTemplate).filter(ReviewTemplate.template_id == template_id).first()
            if template:
                common_templates.append({"template": template.text, "count": count})

        return jsonify({
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "common_templates": common_templates,
            "total_activities": total_activities
        })

@review_bp.route("/evaluate", methods=["GET"])
def render_evaluate_page():
    activity_id = request.args.get("activity_id")
    member_id = request.args.get("member_id")
    return render_template("evaluate.html", activity_id=activity_id, member_id=member_id)

#抓罐頭訊息
@review_bp.route("/api/review_templates", methods=["GET"])
def get_review_templates():
    stars = request.args.get("stars", type=int)
    with get_db() as db_session:
        results = db_session.query(ReviewTemplate).filter(ReviewTemplate.type == stars).all()
        return jsonify([
            {"template_id": r.template_id, "type": r.type, "text": r.text}
            for r in results
        ])




#抓活動參與者（含活動發起人）
@review_bp.route("/api/activities/<int:activity_id>/participants", methods=["GET"])
def get_activity_participants(activity_id):
    participants = []
    with get_db() as db_session:
        # 先抓活動發起人
        activity = db_session.query(Activity).filter(Activity.activity_id == activity_id).first()
        if activity and activity.organizer_id:
            host = db_session.query(Member).filter(Member.member_id == activity.organizer_id).first()
            if host:
                participants.append({
                    "user_id": str(host.member_id),
                    "name": host.name,
    })


        # 再抓報名成功的參加者
        joins = db_session.query(ActivityJoin).filter(
            ActivityJoin.activity_id == activity_id,
            ActivityJoin.status == 'joined'
        ).all()
        for j in joins:
            user = db_session.query(Member).filter(Member.member_id == j.member_id).first()
            if user and all(u["user_id"] != str(user.member_id) for u in participants):
                participants.append({
                    "user_id": str(user.member_id),
                    "name": user.name,
    })


    return jsonify(participants)


# 儲存活動評價
@review_bp.route("/api/activity_reviews", methods=["POST"])
def create_activity_review():
    data = request.get_json()
    with get_db() as db_session:
        review = ActivityReview(
            activity_id=data["activity_id"],
            reviewer_id=data["member_id"],
            rating=data["stars"],  # ✅ 對應 models 裡的 rating 欄位
            template_ids=data.get("tags", []),
            created_time=datetime.now()
        )
        db_session.add(review)
        db_session.commit()
    return jsonify({"status": "success"})


# 儲存對其他參加者的評價（批次）
@review_bp.route("/api/user_reviews/bulk", methods=["POST"])
def create_user_reviews_bulk():
    reviews = request.get_json()
    with get_db() as db_session:
        for r in reviews:
            review = UserReview(
                activity_id=r["activity_id"],
                reviewer_id=r["member_id"],
                target_member_id=r["target_user_id"],
                rating=r["stars"],  # ✅ 對應 models 裡的 rating 欄位
                template_ids=r.get("tags", []),
                created_time=datetime.now()
            )
            db_session.add(review)
        db_session.commit()
    return jsonify({"status": "success"})
