from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from app.database import get_db
from app.models.class_model import Class
from app.models.sport_type import SportType

class_bp = Blueprint("class_bp", __name__, url_prefix="/api/classes")

# 建立課程
@class_bp.route("", methods=["POST"])
def create_class():
    payload = request.get_json()
    with get_db() as db:
        cls = Class(
            title=payload["title"],
            start_time=datetime.fromisoformat(payload["start_time"]),
            end_time=datetime.fromisoformat(payload["end_time"]),
            location_name=payload.get("location_name"),
            location_lat=payload.get("location_lat"),
            location_lng=payload.get("location_lng"),
            max_participants=payload.get("max_participants"),
            venue_fee=payload.get("venue_fee"),
            registration_deadline=datetime.fromisoformat(payload["registration_deadline"]),
            organizer_id=payload["organizer_id"],
            level=payload.get("level"),
            sport_type_id=payload["sport_type_id"],
            description=payload.get("description"),
            status=payload.get("status", "open"),
            target_identity=payload.get("target_identity", "不限"),
            gender=payload.get("gender", "不限"),
            age_range=payload.get("age_range", "不限"),
            created_at=datetime.now()
        )
        db.add(cls)
        db.commit()
        db.refresh(cls)
    return jsonify({"class_id": cls.class_id}), 201

# 查詢所有課程
@class_bp.route("", methods=["GET"])
def list_classes():
    with get_db() as db:
        classes = db.query(Class).filter(Class.status != "closed").all()
        result = []
        for c in classes:
            result.append({
                "class_id": c.class_id,
                "title": c.title,
                "start_time": c.start_time.isoformat() if c.start_time else None,
                "end_time": c.end_time.isoformat() if c.end_time else None,
                "location_name": c.location_name,
                "sport_name": c.sport_type.name if c.sport_type else "未分類",
            })
    return jsonify(result), 200

# 查詢單一課程詳情
@class_bp.route("/details", methods=["GET"])
def get_class_details():
    class_id = request.args.get("class_id")
    if not class_id:
        return jsonify({"error": "缺少 class_id"}), 400

    with get_db() as db:
        cls = db.query(Class).filter(Class.class_id == class_id).first()
        if not cls:
            return jsonify({"error": "課程不存在"}), 404

        return jsonify({
            "class_id": cls.class_id,
            "title": cls.title,
            "sport_name": cls.sport_type.name if cls.sport_type else "未分類",
            "start_time": cls.start_time.isoformat() if cls.start_time else None,
            "end_time": cls.end_time.isoformat() if cls.end_time else None,
            "location_name": cls.location_name,
            "location_lat": cls.location_lat,
            "location_lng": cls.location_lng,
            "max_participants": cls.max_participants,
            "venue_fee": float(cls.venue_fee) if cls.venue_fee else None,
            "registration_deadline": cls.registration_deadline.isoformat() if cls.registration_deadline else None,
            "organizer_id": cls.organizer_id,
            "level": cls.level,
            "sport_type_id": cls.sport_type_id,
            "description": cls.description,
            "status": cls.status,
            "target_identity": cls.target_identity,
            "gender": cls.gender,
            "age_range": cls.age_range,
            "created_at": cls.created_at.isoformat() if cls.created_at else None
        }), 200

# （可選）課程詳情頁面
@class_bp.route("/details_page", methods=["GET"])
def class_details_page():
    return render_template("class_details.html")
