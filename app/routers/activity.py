from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import get_db
from app.models.activity import Activity
from app.models.sport_type import SportType
from app.models.activity_join import ActivityJoin 
from flask import render_template

activity_bp = Blueprint("activity", __name__, url_prefix="/api/activities")


@activity_bp.route("", methods=["POST"])
def create_activity():
    payload = request.get_json()
    with get_db() as db:
        act = Activity(
            title=payload["title"],
            time=datetime.fromisoformat(payload["time"]),
            location_name=payload.get("location_name"),
            location_lat=payload.get("location_lat"),
            location_lng=payload.get("location_lng"),
            max_participants=payload.get("max_participants"),
            organizer_id=payload["organizer_id"],
            level=payload.get("level"),
            sport_type_id=payload["sport_type_id"],
            description=payload.get("description"),
            status=payload.get("status", "open"),
            created_at=datetime.utcnow(),
            has_review=payload.get("has_review", False),
        )
        db.add(act)
        db.commit()
        db.refresh(act)
    return jsonify({"activity_id": act.activity_id}), 201

@activity_bp.route("/overview", methods=["GET"])
def activity_overview():
    with get_db() as db:
        activities = db.query(Activity).all()
    return render_template("activities_overview.html", activities=activities)


@activity_bp.route("", methods=["GET"])
def list_activities():
    with get_db() as db:
        activities = db.query(Activity).all()
        result = []
        for a in activities:
            result.append({
                "activity_id": a.activity_id,
                "title": a.title,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "location_name": a.location_name,
                "sport_name": a.sport_type.name if a.sport_type else "未分類",
            })
    return jsonify(result), 200

@activity_bp.route("/my", methods=["GET"])
def list_my_activities():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
        activities = db.query(Activity).filter(Activity.organizer_id == member_id).join(SportType).all()
        result = []
        for a in activities:
            result.append({
                "activity_id": a.activity_id,
                "title": a.title,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "location_name": a.location_name,
                "sport_name": a.sport_type.name if a.sport_type else "未分類",
            })
    return jsonify(result), 200

@activity_bp.route("/details", methods=["GET"])
def get_activity_details():
    activity_id = request.args.get("activity_id")
    if not activity_id:
        return jsonify({"error": "缺少 activity_id"}), 400

    with get_db() as db:
        activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
        if not activity:
            return jsonify({"error": "活動不存在"}), 404

        return jsonify({
            "activity_id": activity.activity_id,
            "title": activity.title,
            "sport_name": activity.sport_type.name if activity.sport_type else "未分類",
            "start_time": activity.start_time.isoformat() if activity.start_time else None,
            "end_time": activity.end_time.isoformat() if activity.end_time else None,
            "location_name": activity.location_name,
            "current_participants": activity.current_participants,  # 假設有這個欄位
            "max_participants": activity.max_participants,
            "status": activity.status,  # 直接使用資料庫中的狀態
            "level": activity.level,
        }), 200
    

@activity_bp.route("/joined", methods=["GET"])
def list_joined_activities():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
        # 查詢該會員參加的活動
        joined_activities = (
            db.query(Activity)
            .join(ActivityJoin, Activity.activity_id == ActivityJoin.activity_id)
            .filter(ActivityJoin.member_id == member_id, ActivityJoin.status == "joined")
            .all()
        )
        result = []
        for a in joined_activities:
            result.append({
                "activity_id": a.activity_id,
                "title": a.title,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "location_name": a.location_name,
                "sport_name": a.sport_type.name if a.sport_type else "未分類",
                "status": a.status,  # 直接使用資料庫中的狀態
            })
    return jsonify(result), 200

@activity_bp.route("/participants", methods=["GET"])
def get_activity_participants():
    activity_id = request.args.get("activity_id")
    if not activity_id:
        return jsonify({"error": "缺少 activity_id"}), 400

    with get_db() as db:
        # 查詢活動
        activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
        if not activity:
            return jsonify({"error": "活動不存在"}), 404

        # 查詢參加者
        participants = (
            db.query(ActivityJoin)
            .filter(ActivityJoin.activity_id == activity_id, ActivityJoin.status == "joined")
            .all()
        )

        # 構建返回資料
        result = {
            "organizer": {
                "member_id": activity.organizer_id,
                "name": activity.organizer.name,  # 假設 Member 模型有 name 欄位
            },
            "participants": [
                {
                    "member_id": p.member_id,
                    "name": p.member.name,  # 假設 Member 模型有 name 欄位
                }
                for p in participants
            ],
        }
    return jsonify(result), 200

