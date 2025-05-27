# app/routers/member.py
import os
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.member import Member
from app.models.sport_preference import SportPreference
from app.models.preference_sport import PreferenceSport
from app.models.preference_time import PreferenceTime
from app.models.sport_type import SportType
from app.models.time_option import TimeOption


member_bp = Blueprint("members", __name__, url_prefix="/api/members")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@member_bp.route("", methods=["POST"])
def create_member():
    payload = request.get_json() or {}
    required = ("email", "password")
    for key in required:
        if key not in payload:
            return jsonify({"error": f"缺少欄位 {key}"}), 400

    with get_db() as db:
        m = Member(
            member_id=payload.get("member_id"),
            email=payload["email"],
            password=payload["password"],
            name=payload.get("name"),
            gender=payload.get("gender"),
            birthdate=payload.get("birthdate"),
            height=payload.get("height"),
            weight=payload.get("weight"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(m)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return jsonify({"error": "Email 重複"}), 400
        db.refresh(m)

    return jsonify({"member_id": m.member_id}), 201


@member_bp.route("", methods=["GET"])
def list_members():
    with get_db() as db:
        members = db.query(Member).all()

    result = []
    for u in members:
        result.append({
            "member_id": u.member_id,
            "email": u.email,
            "name": u.name,
            "gender": u.gender,
            "birthdate": u.birthdate.isoformat() if u.birthdate else None,
            "height": u.height,
            "weight": u.weight,
            "avatar_url": u.avatar_url,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
        })
    return jsonify(result), 200


@member_bp.route("/<string:member_id>", methods=["GET"])
def get_member(member_id):
    with get_db() as db:
        u = db.get(Member, member_id)
        if not u:
            return jsonify({"error": "找不到該會員"}), 404

        # 基本資料先放入字典
        member_data = {
            "member_id": u.member_id,
            "email": u.email,
            "name": u.name,
            "gender": u.gender,
            "birthdate": u.birthdate.isoformat() if u.birthdate else None,
            "height": u.height,
            "weight": u.weight,
            "city": u.city,
            "area": u.area,
            "avatar_url": u.avatar_url,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
        }

        # 嘗試查詢該會員的偏好資料
        preference = db.query(SportPreference).filter_by(member_id=member_id).first()
        if preference:
            # 運動種類名稱列表
            sports = db.query(SportType.name).join(
                PreferenceSport, PreferenceSport.sport_type_id == SportType.sport_type_id
            ).filter(PreferenceSport.preference_id == preference.preference_id).all()
            sport_names = [s.name for s in sports]

            # 運動時段分類
            time_labels = db.query(TimeOption.label).join(
                PreferenceTime, PreferenceTime.time_id == TimeOption.time_id
            ).filter(PreferenceTime.preference_id == preference.preference_id).all()

            weekday = []
            weekend = []
            for t in time_labels:
                if "週末" in t.label:
                    weekend.append(t.label.replace("週末", ""))
                else:
                    weekday.append(t.label.replace("平日", ""))

            # 加入 sport_preferences 區塊
            member_data["sport_preferences"] = {
                "sports": sport_names,
                "match_gender": preference.match_gender,
                "match_age": preference.match_age,
                "times": {
                    "weekday": weekday,
                    "weekend": weekend
                }
            }

        return jsonify(member_data), 200



@member_bp.route("/login", methods=["POST"])
def login_member():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "請輸入 email 與 password"}), 400

    with get_db() as db:
        user = db.query(Member).filter_by(email=email, password=password).first()

    if not user:
        return jsonify({"error": "帳號或密碼錯誤"}), 401

    return jsonify({
        "member_id": user.member_id,
        "email": user.email,
        "name": user.name,
        "is_first_login": user.is_first_login,
        "is_unfinish_preference": user.is_unfinish_preference
    }), 200


@member_bp.route("/<string:member_id>", methods=["PUT"])
def update_member(member_id):
    updatable = ("name", "gender", "birthdate", "city", "area", "height", "weight")

    is_multipart = request.content_type and request.content_type.startswith("multipart/form-data")
    if is_multipart:
        form = request.form
        data = {k: form[k] for k in updatable if k in form and form[k]}
        file = request.files.get("avatar")
    else:
        json_data = request.get_json() or {}
        data = {k: json_data[k] for k in updatable if k in json_data}
        file = None

    if not data and not file:
        return jsonify({"error": "沒有可更新的欄位或檔案"}), 400

    saved_avatar_url = None

    with get_db() as db:
        m = db.query(Member).get(member_id)
        if not m:
            return jsonify({"error": "找不到該會員"}), 404

        for k, v in data.items():
            if k == "birthdate" and isinstance(v, str):
                try:
                    v = datetime.fromisoformat(v).date()
                except ValueError:
                    return jsonify({"error": "birthdate 格式錯誤，請用 YYYY-MM-DD"}), 400
            elif k in ("height", "weight"):
                try:
                    v = int(v)
                except ValueError:
                    return jsonify({"error": f"{k} 必須是整數"}), 400
            setattr(m, k, v)

        if file and allowed_file(file.filename):
            filename = f"{member_id}.png"
            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)
            save_path = os.path.join(upload_folder, filename)
            file.save(save_path)
            m.avatar_url = f"avatars/{filename}"

        if m.is_first_login:
            m.is_first_login = False

        m.updated_at = datetime.utcnow()

        try:
            db.commit()
            saved_avatar_url = m.avatar_url
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True, "avatar_url": saved_avatar_url}), 200


@member_bp.route("/<string:member_id>", methods=["DELETE"])
def delete_member(member_id):
    with get_db() as db:
        # 查找會員資料
        m = db.query(Member).get(member_id)
        if not m:
            return jsonify({"error": "找不到該會員"}), 404

        # 找到該會員對應的 preference
        preference = db.query(SportPreference).filter(SportPreference.member_id == member_id).first()
        if preference:
            preference_id = preference.preference_id  # 使用 preference_id 作為主鍵
            
            # 刪除 sport_preference 表中與該 preference_id 相關的資料
            sport_preference = db.query(SportPreference).filter(SportPreference.preference_id == preference_id).first()
            if sport_preference:
                db.delete(sport_preference)
            
            # 刪除 preference_sport 表中與該 preference_id 相關的資料
            preference_sport = db.query(PreferenceSport).filter(PreferenceSport.preference_id == preference_id).all()
            for ps in preference_sport:
                db.delete(ps)

            # 刪除 preference_time 表中與該 preference_id 相關的資料
            preference_time = db.query(PreferenceTime).filter(PreferenceTime.preference_id == preference_id).all()
            for pt in preference_time:
                db.delete(pt)

        # 刪除對應頭像圖片
        if m.avatar_url:
            image_path = os.path.join(current_app.root_path, 'static', m.avatar_url)
            if os.path.exists(image_path):
                os.remove(image_path)

        # 刪除會員資料
        db.delete(m)
        db.commit()

    return jsonify({"success": True}), 200


@member_bp.route("/<string:member_id>/full-update", methods=["PUT"])
def update_member_full(member_id):
    data = request.get_json()
    print("收到資料：", data)
    
    height = data.get("height")
    weight = data.get("weight")
    city = data.get("city")
    area = data.get("area")
    pref = data.get("sport_preferences", {})

    sports = pref.get("sports", [])
    match_gender = pref.get("match_gender")
    match_age = pref.get("match_age")
    weekday_times = pref.get("times", {}).get("weekday", [])
    weekend_times = pref.get("times", {}).get("weekend", [])

    with get_db() as db:
        member = db.query(Member).get(member_id)
        if not member:
            return jsonify({"error": "會員不存在"}), 404

        member.height = height
        member.weight = weight
        member.city = city
        member.area = area
        db.add(member)

        db.query(PreferenceSport).filter(
            PreferenceSport.preference_id.in_(
                db.query(SportPreference.preference_id).filter_by(member_id=member_id)
            )
        ).delete(synchronize_session=False)
        
        db.query(PreferenceTime).filter(
            PreferenceTime.preference_id.in_(
                db.query(SportPreference.preference_id).filter_by(member_id=member_id)
            )
        ).delete(synchronize_session=False)

        db.query(SportPreference).filter_by(member_id=member_id).delete()

        sport_pref = SportPreference(
            member_id=member_id,
            match_gender=match_gender,
            match_age=match_age
        )
        db.add(sport_pref)
        db.flush()

        for sport_id in sports:
            db.add(PreferenceSport(preference_id=sport_pref.preference_id, sport_type_id=int(sport_id)))
        for tid in weekday_times + weekend_times:
            db.add(PreferenceTime(preference_id=sport_pref.preference_id, time_id=int(tid)))


        db.commit()

    return jsonify({"message": "會員資料更新成功"})

@member_bp.route("/<string:member_id>/avatar", methods=["POST"])
def update_avatar(member_id):
    if "avatar" not in request.files:
        return jsonify({"error": "缺少頭像檔案"}), 400

    file = request.files["avatar"]
    if not file:
        return jsonify({"error": "無效的檔案"}), 400

    filename = f"{member_id}.png"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)

    file.save(save_path)
    return jsonify({"message": "頭像更新成功"}), 200

@member_bp.route("/check-name", methods=["GET"])
def check_name():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "缺少名稱"}), 400

    with get_db() as db:
        existing_member = db.query(Member).filter_by(name=name).first()
        return jsonify({"available": existing_member is None}), 200
    
@member_bp.route("/check-email", methods=["GET"])
def check_email():
    email = request.args.get("email", "").strip()
    if not email:
        return jsonify({"error": "缺少電子郵件"}), 400

    with get_db() as db:
        existing_member = db.query(Member).filter_by(email=email).first()
        return jsonify({"available": existing_member is None}), 200


