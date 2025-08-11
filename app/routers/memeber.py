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
from app.models.activity import Activity
from app.models.activity_favorite import ActivityFavorite
from app.models.activity_join import ActivityJoin
from app.models.activity_review import ActivityReview
from app.models.user_review import UserReview
from app.models.blacklist import Blacklist


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
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            "public_intro": u.public_intro,
            "facebook_url": u.facebook_url,
            "instagram_url": u.instagram_url,

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

        if m.is_first_login:
            m.is_first_login = False

        m.updated_at = datetime.utcnow()

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True}), 200


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

@member_bp.route("/<string:member_id>/delete-account", methods=["DELETE"])
def delete_account(member_id):
    with get_db() as db:
        # 刪除 member 表中對應的資料
        member = db.query(Member).get(member_id)
        if not member:
            return jsonify({"error": "找不到該會員"}), 404

        # 檢查是否有 open 或 ongoing 狀態的活動
        open_or_ongoing_activities = db.query(Activity).filter(
            Activity.organizer_id == member_id,
            Activity.status.in_(["open", "ongoing"])
        ).count()

        if open_or_ongoing_activities > 0:
            return jsonify({"error": "無法刪除帳號，因為有進行中的活動"}), 400

        # 將活動狀態為 close 的 organizer_id 設為 NULL
        db.query(Activity).filter(
            Activity.organizer_id == member_id,
            Activity.status == "close"
        ).update({"organizer_id": None})

        # 刪除 activity_favorite 表中對應的資料
        db.query(ActivityFavorite).filter(ActivityFavorite.member_id == member_id).delete()

        # 刪除 activity_joins 表中對應的資料
        db.query(ActivityJoin).filter(ActivityJoin.member_id == member_id).delete()

        # 將 activity_review 表中 reviewer_id 設為 NULL
        db.query(ActivityReview).filter(ActivityReview.reviewer_id == member_id).update({"reviewer_id": None})

        # 刪除 sport_preference 表中對應的資料
        preferences = db.query(SportPreference).filter(SportPreference.member_id == member_id).all()
        for preference in preferences:
            # 刪除 preference_sport 表中對應的資料
            db.query(PreferenceSport).filter(PreferenceSport.preference_id == preference.preference_id).delete()
            # 刪除 preference_time 表中對應的資料
            db.query(PreferenceTime).filter(PreferenceTime.preference_id == preference.preference_id).delete()
            # 刪除 sport_preference 資料
            db.delete(preference)

        # 將 user_views 表中 reviewer_id 設為 NULL
        db.query(UserReview).filter(UserReview.reviewer_id == member_id).update({"reviewer_id": None})
        # 刪除 user_views 表中 target_member_id 對應的資料
        db.query(UserReview).filter(UserReview.target_member_id == member_id).delete()

        # 刪除會員資料
        db.delete(member)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True}), 200

@member_bp.route("/change-password", methods=["POST"])
def change_password():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少會員 ID"}), 400

    data = request.get_json() or {}
    new_password = data.get("password")

    if not new_password:
        return jsonify({"error": "缺少新的密碼"}), 400

    with get_db() as db:
        member = db.query(Member).get(member_id)
        if not member:
            return jsonify({"error": "會員不存在"}), 404

        if member.password == new_password:
            return jsonify({"error": "新密碼不能與舊密碼相同"}), 400

        member.password = new_password
        member.updated_at = datetime.utcnow()

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True}), 200

@member_bp.route("/blacklist", methods=["GET"])
def get_blacklist():
    """取得特定會員的黑名單列表"""
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少會員 ID"}), 400

    with get_db() as db:
        blacklists = db.query(Blacklist).filter_by(member_id=member_id).all()

    if not blacklists:
        return jsonify({"error": "該會員沒有黑名單記錄"}), 404

    result = []
    for b in blacklists:
        blocked_member = db.query(Member).filter_by(member_id=b.blocked_member_id).first()
        result.append({
            "blocked_member_id": b.blocked_member_id,
            "blocked_member_name": blocked_member.name if blocked_member else "未知",
            "reason": b.reason,
            "created_at": b.created_at.isoformat() if b.created_at else None
        })

    return jsonify(result), 200

@member_bp.route("/blacklist/unblock", methods=["POST"])
def unblock_member():
    """解除封鎖指定會員"""
    data = request.get_json() or {}
    member_id = data.get("member_id")
    blocked_member_id = data.get("blocked_member_id")

    if not member_id or not blocked_member_id:
        return jsonify({"error": "缺少必要的參數"}), 400

    with get_db() as db:
        blacklist_entry = db.query(Blacklist).filter_by(
            member_id=member_id, blocked_member_id=blocked_member_id
        ).first()

        if not blacklist_entry:
            return jsonify({"error": "找不到封鎖記錄"}), 404

        db.delete(blacklist_entry)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True}), 200


# 新增：將使用者加入黑名單
@member_bp.route("/blacklist/block", methods=["POST"])
def block_member():
    """將指定會員加入黑名單"""
    data = request.get_json() or {}
    member_id = data.get("member_id")
    blocked_member_id = data.get("blocked_member_id")
    reason = data.get("reason")

    if not member_id or not blocked_member_id:
        return jsonify({"error": "缺少必要的參數"}), 400

    with get_db() as db:
        # 檢查是否已經在黑名單
        exists = db.query(Blacklist).filter_by(
            member_id=member_id, blocked_member_id=blocked_member_id
        ).first()
        if exists:
            return jsonify({"error": "該會員已在黑名單中"}), 400

        new_entry = Blacklist(
            member_id=member_id,
            blocked_member_id=blocked_member_id,
            reason=reason
        )
        db.add(new_entry)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True}), 201

@member_bp.route("/<string:member_id>/public-intro", methods=["POST"])
def update_public_intro(member_id):
    import re

    def is_valid_facebook(url):
        # 支援 https://www.facebook.com/xxx 或 https://facebook.com/xxx
        return bool(url) and re.match(r"^https?://(www\.)?facebook\.com/[A-Za-z0-9_.-]+/?$", url)

    def is_valid_instagram(url):
        # 支援 https://www.instagram.com/xxx 或 https://instagram.com/xxx
        return bool(url) and re.match(r"^https?://(www\.)?instagram\.com/[A-Za-z0-9_.-]+/?$", url)

    data = request.get_json() or {}
    public_intro = data.get("public_intro") if "public_intro" in data else None
    fb_link = data.get("fb_link") if "fb_link" in data else data.get("facebook_url") if "facebook_url" in data else None
    ig_link = data.get("ig_link") if "ig_link" in data else data.get("instagram_url") if "instagram_url" in data else None


    # public_intro 必須有提供（即使是空字串也可）
    if public_intro is None:
        return jsonify({"error": "缺少自我介紹內容"}), 400

    with get_db() as db:
        member = db.query(Member).get(member_id)
        if not member:
            return jsonify({"error": "找不到該會員"}), 404
        member.public_intro = public_intro
        # 若有提供 facebook/ig 欄位（即使是空字串），就更新
        if fb_link is not None:
            if fb_link == "":
                member.facebook_url = None
            else:
                if not is_valid_facebook(fb_link):
                    return jsonify({"error": "Facebook 連結格式錯誤，請輸入 https://www.facebook.com/用戶名"}), 400
                member.facebook_url = fb_link
        if ig_link is not None:
            if ig_link == "":
                member.instagram_url = None
            else:
                if not is_valid_instagram(ig_link):
                    return jsonify({"error": "Instagram 連結格式錯誤，請輸入 https://www.instagram.com/用戶名"}), 400
                member.instagram_url = ig_link
        member.updated_at = datetime.utcnow()
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True}), 200

# 取得指定會員的通知列表
@member_bp.route("/<string:member_id>/notifications", methods=["GET"])
def get_member_notifications(member_id):
    with get_db() as db:
        from app.models.notification import Notification
        notifications = db.query(Notification).filter_by(member_id=member_id).order_by(Notification.created_at.desc()).all()
        result = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in notifications
        ]
    return jsonify(result), 200

@member_bp.route("/notifications/<int:notification_id>/read", methods=["PATCH"])
def mark_notification_read(notification_id):
    with get_db() as db:
        from app.models.notification import Notification
        notification = db.query(Notification).filter_by(id=notification_id).first()
        if not notification:
            return jsonify({"error": "通知不存在"}), 404
        notification.is_read = True
        db.commit()
    return jsonify({"message": "已標記為已讀"}), 200




