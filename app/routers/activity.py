from flask import Blueprint, request, jsonify ,render_template
from datetime import datetime ,timedelta
from app.database import get_db
from app.models.activity import Activity
from app.models.sport_type import SportType
from app.models.activity_join import ActivityJoin 
from app.models.course_schedul import CourseSchedule




activity_bp = Blueprint("activity", __name__, url_prefix="/api/activities")


@activity_bp.route("", methods=["POST"])
def create_activity():
    payload = request.get_json()
    with get_db() as db:
        act = Activity(
            title=payload["title"],
            type="activity",
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

@activity_bp.route("/class", methods=["POST"])
def create_class():
    payload = request.get_json()
    with get_db() as db:
        act = Activity(
            title=payload["title"],
            type="class",
            start_time=datetime.fromisoformat(payload["start_time"]),
            end_time=datetime.fromisoformat(payload["end_time"]),
            location_name=payload.get("location_name"),
            location_lat=payload.get("location_lat"),
            location_lng=payload.get("location_lng"),
            max_participants=payload.get("max_participants"),
            current_participants=0,
            organizer_id=payload["organizer_id"],
            level=payload.get("level", None),
            sport_type_id=payload["sport_type_id"],
            description=payload.get("description"),
            status=payload.get("status", "open"),
            created_at=datetime.now(),
            has_review=False,
            target_identity=payload.get("target_identity", "不限"),
            gender=payload.get("gender", None),
            age_range=payload.get("age_range", None),
            venue_fee=payload.get("venue_fee"),
            registration_deadline=datetime.fromisoformat(payload["registration_deadline"]),
        )
        db.add(act)
        db.commit()
        db.refresh(act)
      
    return jsonify({"activity_id": act.activity_id}), 201

@activity_bp.route("/multiclass", methods=["POST"])
def create_multiclass():
    try:
        payload = request.get_json()

        # 檢查必要欄位是否存在
        required_fields = ["first_time", "weekdays", "multi_count", "every_starttime", "every_endtime", "title", "organizer_id", "registration_deadline"]
        for field in required_fields:
            if field not in payload:
                return jsonify({"error": f"缺少必要欄位: {field}"}), 400

        # 定義中文數字到整數的映射
        chinese_to_int = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "日": 7,
        }

        # 解析前端資料
        try:
            start_date = datetime.fromisoformat(payload["first_time"])  # 活動開始時間
            weekdays = [chinese_to_int[day] for day in payload["weekdays"]]  # 星期幾，轉換中文數字為整數
            multi_count = int(payload["multi_count"])  # 課程總堂數
            start_time = datetime.strptime(payload["every_starttime"], "%H:%M").time()  # 每堂課的開始時間
            end_time = datetime.strptime(payload["every_endtime"], "%H:%M").time()  # 每堂課的結束時間
            registration_deadline = datetime.fromisoformat(payload["registration_deadline"])
        except KeyError as e:
            return jsonify({"error": f"無效的星期值: {str(e)}"}), 400
        except ValueError as e:
            return jsonify({"error": f"資料格式錯誤: {str(e)}"}), 400

        # 計算每堂課的日期
        class_dates = []  # 用來存儲每次上課的日期
        current_date = start_date

        # 根據 weekdays 計算每堂課的日期
        while len(class_dates) < multi_count:
            # 檢查當前日期是否符合需要的上課星期
            if current_date.weekday() + 1 in weekdays:  # weekday() 返回 0-6，星期一是 0
                class_dates.append(current_date)
            current_date += timedelta(days=1)  # 增加一天，檢查下個日期

        # 計算活動結束時間，使用最後一堂課的時間
        activity_end_time = datetime.combine(class_dates[-1], end_time)  # 用最後一堂課的時間作為活動結束時間

        # 創建活動並添加至 session 中
        with get_db() as db:
            try:
                act = Activity(
                    title=payload["title"],
                    type="muti_class",
                    sport_type_id=payload["sport_type_id"],
                    start_time=start_date,
                    end_time=activity_end_time,
                    location_name=payload.get("location_name"),
                    location_lat=payload.get("location_lat"),
                    location_lng=payload.get("location_lng"),
                    max_participants=payload.get("max_participants"),
                    current_participants=0,
                    organizer_id=payload["organizer_id"],
                    description=payload.get("description"),
                    status=payload.get("status", "open"),
                    created_at=datetime.now(),
                    venue_fee=payload.get("venue_fee"),
                    registration_deadline=registration_deadline,
                )
                db.add(act)
                db.flush()  # 強制刷新，確保 activity_id 被生成並寫入資料庫

                # 根據 multi_count 和 weekdays 生成課程安排 (CourseSchedule)
                for idx, session_date in enumerate(class_dates):
                    # 確保 start_time 和 end_time 轉換為 datetime 型別
                    start_datetime = datetime.combine(session_date.date(), start_time)
                    end_datetime = datetime.combine(session_date.date(), end_time)

                    course_schedule = CourseSchedule(
                        activity_id=act.activity_id,  # 正確關聯活動
                        session_number=idx + 1,
                        weekday=session_date.strftime("%A"),
                        start_time=start_datetime,
                        end_time=end_datetime,
                        start_date=session_date.date()
                    )
                    db.add(course_schedule)  # 將課程安排加入 session 中

                db.commit()
                db.refresh(act)  # 一次性提交所有操作

            except Exception as e:
                db.rollback()  # 如果有錯誤發生，回滾所有操作
                return jsonify({"error": f"資料創建失敗: {str(e)}"}), 500

        return jsonify({"activity_id": act.activity_id}), 201

    except Exception as e:
        return jsonify({"error": f"伺服器錯誤: {str(e)}"}), 500

@activity_bp.route("/overview", methods=["GET"])
def activity_overview():
    with get_db() as db:
        activities = db.query(Activity).all()
    return render_template("activities_overview.html", activities=activities)


@activity_bp.route("", methods=["GET"])
def list_activities():
    with get_db() as db:
        activities = db.query(Activity).filter(Activity.status != "close").all()
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
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "location_name": a.location_name,
                "sport_name": a.sport_type.name if a.sport_type else "未分類",
                "registration_deadline": a.registration_deadline.isoformat() if a.registration_deadline else None,
                "status": a.status,
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
            "type": activity.type,
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
                "registration_deadline": a.registration_deadline.isoformat() if a.registration_deadline else None,
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
        joined_participants = (
            db.query(ActivityJoin)
            .filter(ActivityJoin.activity_id == activity_id, ActivityJoin.status == "joined")
            .all()
        )

        pending_participants = (
            db.query(ActivityJoin)
            .filter(ActivityJoin.activity_id == activity_id, ActivityJoin.status == "pending")
            .all()
        )

        # 構建返回資料
        result = {
            "organizer": {
                "member_id": activity.organizer_id,
                "name": activity.organizer.name,
            },
            "joined_participants": [
                {
                    "member_id": p.member_id,
                    "name": p.member.name,
                }
                for p in joined_participants
            ],
            "pending_participants": [
                {
                    "member_id": p.member_id,
                    "name": p.member.name,
                }
                for p in pending_participants
            ],
        }
    return jsonify(result), 200

@activity_bp.route("/cancel", methods=["POST"])
def cancel_participation():
    data = request.get_json()
    member_id = data.get("member_id")
    activity_id = data.get("activity_id")

    if not member_id or not activity_id:
        return jsonify({"error": "缺少必要參數"}), 400

    with get_db() as db:
        # 查找該會員參加的活動記錄
        activity_join = db.query(ActivityJoin).filter_by(member_id=member_id, activity_id=activity_id).first()
        if not activity_join:
            return jsonify({"error": "未找到參加記錄"}), 404

        # 刪除參加記錄
        db.delete(activity_join)

        # 更新活動的 current_participants
        activity = db.query(Activity).filter_by(activity_id=activity_id).first()
        if activity and activity.current_participants > 0:
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
        try:
            participant = (
                db.query(ActivityJoin)
                .filter(ActivityJoin.activity_id == activity_id, ActivityJoin.member_id == member_id)
                .first()
            )

            if not participant:
                # 添加詳細日誌
                return jsonify({"error": f"參加者記錄不存在，activity_id: {activity_id}, member_id: {member_id}"}), 404

            if new_status == "joined" and participant.status == "pending":
                # 獲取活動資訊
                activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
                if activity:
                    # 只有 open 或 deadline 狀態允許同意
                    if activity.status not in ["open", "deadline"]:
                        return jsonify({"error": "活動已開始，無法增加參加者"}), 403
                    # 如果人數已達上限，阻止執行
                    if activity.current_participants >= activity.max_participants:
                        return jsonify({"error": "活動已額滿，無法增加參加者"}), 403

                    # 更新活動的 current_participants
                    activity.current_participants += 1

            participant.status = new_status
            db.commit()
        except Exception as e:
            # 捕獲並記錄例外情況
            return jsonify({"error": f"伺服器錯誤: {str(e)}"}), 500

    return jsonify({"message": "狀態更新成功"}), 200


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

         # 檢查是否為活動的發起人
        if activity.organizer_id == member_id:
            return jsonify({"error": "主辦人無法申請參加自己的活動"}), 403
        
        # 只有 open 或 deadline 狀態允許報名，其他狀態一律拒絕
        if activity.status not in ["open", "deadline"]:
            return jsonify({"error": "報名已截止，無法申請參加"}), 403


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

