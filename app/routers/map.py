# app/routers/map.py
from flask import Blueprint, render_template, request
import os
from flask import jsonify
from app.database import get_db
from app.models.activity import Activity
from app.models.sport_type import SportType

map_bp = Blueprint("map", __name__)

# ✅ 新增縣市邊界範圍（只放常用幾個做示範）
county_bounds = {
    "台北市":    {"min_lat": 25.00, "max_lat": 25.15, "min_lng": 121.45, "max_lng": 121.60},
    "新北市":    {"min_lat": 24.80, "max_lat": 25.30, "min_lng": 121.20, "max_lng": 121.70},
    "桃園市":    {"min_lat": 24.80, "max_lat": 25.10, "min_lng": 121.00, "max_lng": 121.40},
    "台中市":    {"min_lat": 24.00, "max_lat": 24.30, "min_lng": 120.50, "max_lng": 121.00},
    "台南市":    {"min_lat": 22.90, "max_lat": 23.10, "min_lng": 120.10, "max_lng": 120.30},
    "高雄市":    {"min_lat": 22.50, "max_lat": 22.90, "min_lng": 120.20, "max_lng": 120.40},
    "基隆市":    {"min_lat": 25.10, "max_lat": 25.20, "min_lng": 121.70, "max_lng": 121.80},
    "新竹市":    {"min_lat": 24.75, "max_lat": 24.85, "min_lng": 120.90, "max_lng": 121.00},
    "新竹縣":    {"min_lat": 24.60, "max_lat": 25.10, "min_lng": 120.70, "max_lng": 121.30},
    "苗栗縣":    {"min_lat": 24.30, "max_lat": 24.70, "min_lng": 120.50, "max_lng": 121.00},
    "彰化縣":    {"min_lat": 23.80, "max_lat": 24.10, "min_lng": 120.30, "max_lng": 120.60},
    "南投縣":    {"min_lat": 23.50, "max_lat": 24.10, "min_lng": 120.70, "max_lng": 121.10},
    "雲林縣":    {"min_lat": 23.60, "max_lat": 23.90, "min_lng": 120.20, "max_lng": 120.50},
    "嘉義市":    {"min_lat": 23.45, "max_lat": 23.55, "min_lng": 120.40, "max_lng": 120.50},
    "嘉義縣":    {"min_lat": 23.30, "max_lat": 23.60, "min_lng": 120.10, "max_lng": 120.60},
    "屏東縣":    {"min_lat": 21.90, "max_lat": 22.80, "min_lng": 120.50, "max_lng": 121.00},
    "宜蘭縣":    {"min_lat": 24.40, "max_lat": 24.90, "min_lng": 121.50, "max_lng": 122.00},
    "花蓮縣":    {"min_lat": 23.50, "max_lat": 24.30, "min_lng": 121.20, "max_lng": 122.00},
    "台東縣":    {"min_lat": 22.30, "max_lat": 23.50, "min_lng": 120.90, "max_lng": 121.50},
    "澎湖縣":    {"min_lat": 23.50, "max_lat": 23.60, "min_lng": 119.50, "max_lng": 119.70},
    "金門縣":    {"min_lat": 24.30, "max_lat": 24.50, "min_lng": 118.20, "max_lng": 118.40},
    "連江縣":    {"min_lat": 26.10, "max_lat": 26.30, "min_lng": 119.90, "max_lng": 120.10}
}

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
    activity_type = request.args.get("type")

    with get_db() as db:
        query = (
            db.query(Activity)
            .filter(Activity.status != "close", Activity.end_time > datetime.now())
        )

        if activity_type and activity_type != "all":
            query = query.filter(Activity.type == activity_type)

        activities = query.join(SportType).all()

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

@map_bp.route("/api/map/markers/by-county", methods=["GET"])
def get_markers_by_county():
    county = request.args.get("county")
    activity_type = request.args.get("type")

    if county == "all":
        return get_active_markers()

    bounds = county_bounds.get(county)
    if not bounds:
        return jsonify([]), 200

    with get_db() as db:
        filters = [
            Activity.status != "close",
            Activity.end_time > datetime.now(),
            Activity.location_lat >= bounds["min_lat"],
            Activity.location_lat <= bounds["max_lat"],
            Activity.location_lng >= bounds["min_lng"],
            Activity.location_lng <= bounds["max_lng"],
        ]

        if activity_type and activity_type != "all":
            filters.append(Activity.type == activity_type)

        activities = (
            db.query(Activity)
            .filter(*filters)
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
                "type": a.type
            })

    return jsonify(result), 200