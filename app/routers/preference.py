from flask import Blueprint, request, jsonify
from app.models import SportType, TimeOption, SportPreference, PreferenceTime, PreferenceSport
from app.database import get_db  # 使用 get_db 來獲取資料庫連線

# 註冊 Blueprint
preference_bp = Blueprint("preferences", __name__, url_prefix="/api/preferences")

# GET /api/preferences/options
@preference_bp.route("/options", methods=["GET"])
def get_preferences_options():
    with get_db() as db:  # 使用 with 語法獲取資料庫會話
        # 查詢所有運動類型
        sport_types = db.query(SportType).all()
        # 查詢所有時間選項
        time_options = db.query(TimeOption).all()

    # 將結果轉換為字典
    sport_types_data = [
        {"sport_type_id": sport.sport_type_id, "name": sport.name}
        for sport in sport_types
    ]
    time_options_data = [
        {"time_id": time.time_id, "label": time.label}
        for time in time_options
    ]
    
    # 返回運動類型和時間選項資料
    return jsonify({
        "sport_types": sport_types_data,
        "time_options": time_options_data
    })

# PUT /api/preferences
@preference_bp.route("", methods=["PUT"])
def update_preferences():
    data = request.get_json()

    member_id = data.get("member_id")
    selected_sports = data.get("sports", [])
    selected_times = data.get("times", [])
    match_gender = data.get("matchGender")
    match_age = data.get("matchAge")
    
    with get_db() as db:  # 使用 with 語法獲取資料庫會話
        # 儲存運動偏好
        sport_preference = SportPreference(
            member_id=member_id,
            match_gender=match_gender,
            match_age=match_age
        )
        db.add(sport_preference)
        db.flush()  # 以便取得自動生成的 preference_id

        # 儲存運動項目選擇
        for sport_id in selected_sports:
            preference_sport = PreferenceSport(
                preference_id=sport_preference.preference_id,
                sport_type_id=sport_id
            )
            db.add(preference_sport)

        # 儲存時間偏好
        for time_id in selected_times:
            preference_time = PreferenceTime(
                preference_id=sport_preference.preference_id,
                time_id=time_id
            )
            db.add(preference_time)
        
        db.commit()  # 提交資料

    return jsonify({"message": "偏好設定已儲存"}), 200
