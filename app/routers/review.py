from flask import Blueprint, request, jsonify
from app.database import get_db
from app.models.user_review import UserReview
from app.models.review_template import ReviewTemplate
from app.models.activity import Activity
from app.models.activity_join import ActivityJoin

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
