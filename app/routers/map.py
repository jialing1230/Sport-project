# app/routers/map.py
from flask import Blueprint, render_template, request
import os
from flask import jsonify
from app.database import get_db
from app.models.activity import Activity
from app.models.sport_type import SportType

map_bp = Blueprint("map", __name__)

@map_bp.route("/news")
def google_map():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    member_id = request.args.get("member_id")
    return render_template("news.html", api_key=api_key, member_id=member_id)
@map_bp.route("/home")
def home_page():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    member_id = request.args.get("member_id")  # ⬅️ 接住 URL 上的 member_id
    return render_template("home.html", api_key=api_key, member_id=member_id)
from datetime import datetime
@map_bp.route("/api/map/active-markers", methods=["GET"])
def get_active_markers():
    with get_db() as db:
        activities = (
            db.query(Activity)
            .filter(Activity.status != "close", Activity.end_time > datetime.now())
            .join(SportType)
            .all()
        )

        result = []
        for a in activities:
            result.append({
                "activity_id": a.activity_id,
                "title": a.title,
                "location_lat": a.location_lat,
                "location_lng": a.location_lng,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "registration_deadline": a.registration_deadline.isoformat() if a.registration_deadline else None,
                "current_participants": a.current_participants,
                "max_participants": a.max_participants,
                "location_name": a.location_name,
                "status": a.status,
                "sport_type": a.sport_type.name if a.sport_type else "未分類",
                "type": a.type  # ✅ 新增這一行（最重要）
            })

    return jsonify(result), 200