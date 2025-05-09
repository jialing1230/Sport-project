from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from app.database import get_db
from app.models.activity import Activity
from app.models.sport_type import SportType
from app.models.activity_join import ActivityJoin

activity_bp = Blueprint("activity", __name__, url_prefix="/api/activities")

@activity_bp.route("", methods=["POST"])
def create_activity():
    payload = request.get_json()
    with get_db() as db:
        act = Activity(
            title=payload["title"],
            start_time=datetime.fromisoformat(payload["start_time"]),
            end_time=datetime.fromisoformat(payload["end_time"]),
            location_name=payload.get("location_name"),
            location_lat=payload.get("location_lat"),
            location_lng=payload.get("location_lng"),
            max_participants=payload.get("max_participants"),
            current_participants=1,
            organizer_id=payload["organizer_id"],
            level=payload.get("level"),
            sport_type_id=payload["sport_type_id"],
            description=payload.get("description"),
            status=payload.get("status", "open"),
            created_at=datetime.now(),
            has_review=False,
            target_identity=payload.get("target_identity", "不限"),
            gender=payload.get("gender", "不限"),
            age_range=payload.get("age_range", "不限"),
            venue_fee=payload.get("venue_fee"),
            registration_deadline=datetime.fromisoformat(payload["registration_deadline"]),
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

@activity_bp.route("/joined", methods=["GET"])
def list_joined_activities():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
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
                "status": a.status
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
            "location_lat": activity.location_lat,
            "location_lng": activity.location_lng,
            "max_participants": activity.max_participants,
            "current_participants": activity.current_participants,
            "organizer_id": activity.organizer_id,
            "level": activity.level,
            "sport_type_id": activity.sport_type_id,
            "description": activity.description,
            "status": activity.status,
            "created_at": activity.created_at.isoformat() if activity.created_at else None,
            "has_review": activity.has_review,
            "target_identity": activity.target_identity,
            "gender": activity.gender,
            "age_range": activity.age_range,
            "venue_fee": float(activity.venue_fee) if activity.venue_fee else None,
            "registration_deadline": activity.registration_deadline.isoformat() if activity.registration_deadline else None,
        }), 200

@activity_bp.route("/details_page", methods=["GET"])
def activity_details_page():
    return render_template("activity_details.html")

@activity_bp.route("/participants", methods=["GET"])
def get_activity_participants():
    activity_id = request.args.get("activity_id")
    if not activity_id:
        return jsonify({"error": "缺少 activity_id"}), 400

    with get_db() as db:
        activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
        if not activity:
            return jsonify({"error": "活動不存在"}), 404

        joined_participants = db.query(ActivityJoin).filter_by(activity_id=activity_id, status="joined").all()
        pending_participants = db.query(ActivityJoin).filter_by(activity_id=activity_id, status="pending").all()

        result = {
            "organizer": {
                "member_id": activity.organizer_id,
                "name": activity.organizer.name,
            },
            "joined_participants": [
                {"member_id": p.member_id, "name": p.member.name} for p in joined_participants
            ],
            "pending_participants": [
                {"member_id": p.member_id, "name": p.member.name} for p in pending_participants
            ],
        }
    return jsonify(result), 200

@activity_bp.route("/join", methods=["POST"])
def join_activity():
    data = request.get_json()
    member_id = data.get("member_id")
    activity_id = data.get("activity_id")

    if not member_id or not activity_id:
        return jsonify({"error": "缺少必要參數"}), 400

    with get_db() as db:
        activity = db.query(Activity).filter_by(activity_id=activity_id).first()
        if not activity:
            return jsonify({"error": "活動不存在"}), 404

        if activity.current_participants >= activity.max_participants:
            return jsonify({"error": "活動已額滿"}), 403

        existing = db.query(ActivityJoin).filter_by(member_id=member_id, activity_id=activity_id).first()
        if existing:
            return jsonify({"error": "已參加或申請過此活動"}), 409

        join = ActivityJoin(
            member_id=member_id,
            activity_id=activity_id,
            status="pending"
        )
        db.add(join)
        db.commit()

    return jsonify({"message": "申請參加成功，等待主辦人確認"}), 200

@activity_bp.route("/cancel", methods=["POST"])
def cancel_participation():
    data = request.get_json()
    member_id = data.get("member_id")
    activity_id = data.get("activity_id")

    if not member_id or not activity_id:
        return jsonify({"error": "缺少必要參數"}), 400

    with get_db() as db:
        join = db.query(ActivityJoin).filter_by(member_id=member_id, activity_id=activity_id).first()
        if not join:
            return jsonify({"error": "找不到參加紀錄"}), 404

        db.delete(join)

        activity = db.query(Activity).filter_by(activity_id=activity_id).first()
        if activity and join.status == "joined" and activity.current_participants > 0:
            activity.current_participants -= 1

        db.commit()

    return jsonify({"message": "已取消參加活動"}), 200

@activity_bp.route("/update_status", methods=["POST"])
def update_participant_status():
    data = request.get_json()
    activity_id = data.get("activity_id")
    member_id = data.get("member_id")
    new_status = data.get("status")

    if not activity_id or not member_id or new_status not in ["joined", "reject"]:
        return jsonify({"error": "缺少必要參數或狀態無效"}), 400

    with get_db() as db:
        participant = db.query(ActivityJoin).filter_by(activity_id=activity_id, member_id=member_id).first()
        if not participant:
            return jsonify({"error": "參加者記錄不存在"}), 404

        if new_status == "joined" and participant.status == "pending":
            activity = db.query(Activity).filter_by(activity_id=activity_id).first()
            if activity:
                activity.current_participants += 1
                if activity.current_participants >= activity.max_participants:
                    activity.status = "close"
                    db.query(ActivityJoin).filter_by(activity_id=activity_id, status="pending").update({"status": "reject"})

        participant.status = new_status
        db.commit()

    return jsonify({"message": "狀態更新成功"}), 200
