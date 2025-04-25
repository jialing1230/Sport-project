from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import get_db
from app.models.activity import Activity

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


@activity_bp.route("", methods=["GET"])
def list_activities():
    with get_db() as db:
        activities = db.query(Activity).all()
    result = [
        {
            "activity_id": a.activity_id,
            "title": a.title,
            "time": a.time.isoformat(),
            "location": a.location_name,
            "status": a.status,
        }
        for a in activities
    ]
    return jsonify(result), 200

@activity_bp.route("/test", methods=["GET"])
def test_activity():
    return jsonify({"message": "活動測試成功！"}), 200

