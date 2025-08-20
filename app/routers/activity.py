from flask import Blueprint, request, jsonify ,render_template
from datetime import datetime 
from app.database import get_db
from app.models.activity import Activity
from app.models.sport_type import SportType
from app.models.activity_join import ActivityJoin 
from app.models.course_schedul import CourseSchedule
from app.models.member import Member
from app.models.activity_favorite import ActivityFavorite




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
            has_review=0,
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

        # 解析前端資料
        try:
            start_date = datetime.fromisoformat(payload["first_time"])  # 活動開始時間
            end_time = datetime.strptime(payload["every_endtime"], "%H:%M").time()  # 每堂課的結束時間
            registration_deadline = datetime.fromisoformat(payload["registration_deadline"])
        except KeyError as e:
            return jsonify({"error": f"無效的星期值: {str(e)}"}), 400
        except ValueError as e:
            return jsonify({"error": f"資料格式錯誤: {str(e)}"}), 400

        # 提取 scheduleList 的日期部分
        schedule_list = payload.get("scheduleList", [])
        if not schedule_list:
            return jsonify({"error": "缺少 scheduleList"}), 400

        class_dates = []  # 用來存儲每次上課的日期
        for schedule in schedule_list:
            date_str = schedule.split(" ")[0]  # 提取日期部分
            class_date = datetime.fromisoformat(date_str)
            class_dates.append(class_date)

        # 計算活動結束時間，使用最後一堂課的時間
        activity_end_time = datetime.combine(class_dates[-1], end_time)  # 用最後一堂課的時間作為活動結束時間

        # 創建活動並添加至 session 中
        with get_db() as db:
            try:
                act = Activity(
                    title=payload["title"],
                    type="muti_class",
                    sport_type_id=payload["sport_type_id"],
                    level=payload.get("level"),
                    gender=payload.get("gender"),
                    age_range=payload.get("age_range"),
                    start_time=start_date,
                    end_time=activity_end_time,
                    location_name=payload.get("location_name"),
                    location_lat=payload.get("location_lat"),
                    location_lng=payload.get("location_lng"),
                    max_participants=payload.get("max_participants"),
                    current_participants=0,
                    has_review=0,
                    target_identity=payload.get("target_identity", "不限"),
                    organizer_id=payload["organizer_id"],
                    description=payload.get("description"),
                    status=payload.get("status", "open"),
                    created_at=datetime.now(),
                    venue_fee=payload.get("venue_fee"),
                    registration_deadline=registration_deadline,              
                )
                db.add(act)
                db.flush()  # 強制刷新，確保 activity_id 被生成並寫入資料庫

                # 根據前端回傳的清單生成課程安排 (CourseSchedule)
                schedule_list = payload.get("scheduleList", [])
                if not schedule_list:
                    return jsonify({"error": "缺少 scheduleList"}), 400

                try:
                    for idx, schedule in enumerate(schedule_list):
                        # 檢查 schedule 格式是否正確
                        if " ~ " not in schedule:
                            return jsonify({"error": f"無效的時間範圍格式: {schedule}"}), 400

                        try:
                            # 補充日期部分，使用 class_dates 中的日期
                            start_datetime_str, end_datetime_str = schedule.split(" ~ ")
                            start_datetime_str = f"{class_dates[idx].date()}T{start_datetime_str.split(' ')[-1]}"  # 使用對應的日期
                            end_datetime_str = f"{class_dates[idx].date()}T{end_datetime_str}"  # 使用對應的日期

                            # 確保 start_datetime_str 和 end_datetime_str 是字串
                            if not isinstance(start_datetime_str, str) or not isinstance(end_datetime_str, str):
                                raise ValueError("時間範圍的格式必須是字串")

                            # 解析 schedule 的開始和結束時間
                            start_datetime = datetime.fromisoformat(start_datetime_str)
                            end_datetime = datetime.fromisoformat(end_datetime_str)
                        except ValueError as e:
                            return jsonify({"error": f"無效的時間格式: {str(e)}"}), 400

                        course_schedule = CourseSchedule(
                            activity_id=act.activity_id,  # 正確關聯活動
                            session_number=idx + 1,
                            weekday=start_datetime.strftime("%A"),
                            start_time=start_datetime,
                            end_time=end_datetime,
                            start_date=start_datetime.date()
                        )
                        db.add(course_schedule)  # 將課程安排加入 session 中

                    db.commit()
                    db.refresh(act)  # 一次性提交所有操作

                except Exception as e:
                    db.rollback()  # 如果有錯誤發生，回滾所有操作
                    return jsonify({"error": f"資料創建失敗: {str(e)}"}), 500

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
            if hasattr(a, 'type') and (a.type == 'class' or a.type == 'muti_class'):
                activity_type = '訓練課程'
            else:
                activity_type = '一般活動'
            course_schedules = []
            if hasattr(a, 'type') and a.type == 'muti_class':
                schedules = db.query(CourseSchedule).filter(CourseSchedule.activity_id == a.activity_id).all()
                course_schedules = [
                    {
                        "session_number": cs.session_number,
                        "weekday": cs.weekday,
                        "start_time": cs.start_time.isoformat() if cs.start_time else None,
                        "end_time": cs.end_time.isoformat() if cs.end_time else None,
                        "start_date": cs.start_date.isoformat() if cs.start_date else None,
                    }
                    for cs in schedules
                ]
            elif hasattr(a, 'type') and a.type == 'class':
                # 單堂課程，直接用活動本身的時間
                course_schedules = [
                    {
                        "session_number": 1,
                        "weekday": a.start_time.strftime("%A") if a.start_time else None,
                        "start_time": a.start_time.isoformat() if a.start_time else None,
                        "end_time": a.end_time.isoformat() if a.end_time else None,
                        "start_date": a.start_time.date().isoformat() if a.start_time else None,
                    }
                ]
            result.append({
                "activity_id": a.activity_id,
                "title": a.title,
                "type": a.type if hasattr(a, 'type') else None,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "location_name": a.location_name,
                "sport_name": a.sport_type.name if a.sport_type else "未分類",
                "level": a.level,
                "organizer_name": a.organizer.name if a.organizer else "",
                "venue_fee": float(a.venue_fee) if a.venue_fee else 0,
                "activity_type": activity_type,
                "course_schedules": course_schedules,
                "registration_deadline": a.registration_deadline.isoformat() if a.registration_deadline else None,
                "current_participants": a.current_participants,
                "max_participants": a.max_participants,
                "status": a.status,
                "gender": a.gender,
                "age_range": a.age_range
            })
    return jsonify(result), 200

@activity_bp.route("/my", methods=["GET"])
def list_my_activities():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
        activities = db.query(Activity).filter(Activity.organizer_id == member_id).join(SportType).join(Member, Member.member_id == Activity.organizer_id).all()
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
                "level": a.level,
                "venue_fee": float(a.venue_fee) if a.venue_fee else 0,
                "type": a.type,
                "organizer": {
                    "name": a.organizer.name if a.organizer else "未知"
                }
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

        organizer = db.query(Member).filter(Member.member_id == activity.organizer_id).first()

        response = {
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
            "organizer": {
                "name": organizer.name if organizer else "未知"
            },
            "level": activity.level,
            "sport_type_id": activity.sport_type_id,
            "description": activity.description,
            "status": activity.status,
            "created_at": activity.created_at.isoformat() if activity.created_at else None,
            "has_review": activity.has_review,
            "target_identity": activity.target_identity,
            "gender": activity.gender,
            "age_range": activity.age_range,
            "venue_fee": float(activity.venue_fee) if activity.venue_fee else 0,
            "registration_deadline": activity.registration_deadline.isoformat() if activity.registration_deadline else None,
        }

        # 如果 type 是 "muti_class"，額外查詢 course_schedul
        if activity.type == "muti_class":
            course_schedules = db.query(CourseSchedule).filter(CourseSchedule.activity_id == activity_id).all()
            response["course_schedules"] = [
                {
                    "session_number": cs.session_number,
                    "weekday": cs.weekday,
                    "start_time": cs.start_time.isoformat() if cs.start_time else None,
                    "end_time": cs.end_time.isoformat() if cs.end_time else None,
                    "start_date": cs.start_date.isoformat() if cs.start_date else None,
                }
                for cs in course_schedules
            ]

        return jsonify(response), 200
    
@activity_bp.route("/details_page", methods=["GET"])
def activity_details_page():
    return render_template("activity_details.html")

@activity_bp.route("/joined_details_page", methods=["GET"])
def joined_activity_detail_page():
    return render_template("joined_activity_detail.html")

@activity_bp.route("/created_details_page", methods=["GET"])
def created_activity_detail_page():
    return render_template("created_activity_detail.html")

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
            .join(Member, Member.member_id == Activity.organizer_id)
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
                "status": a.status,
                "level": a.level,
                "venue_fee": float(a.venue_fee) if a.venue_fee else None,
                "type": a.type,
                "organizer": {
                "name": a.organizer.name if a.organizer else "未知"
                }
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
                "has_review": activity.has_review
            },
            "joined_participants": [
                {
                    "member_id": p.member_id,
                    "name": p.member.name,
                    "has_review": getattr(p, "has_review", False),
                    "is_checked_in": p.is_checked_in,
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

        # 查找會員名稱
        member = db.query(Member).filter_by(member_id=member_id).first()
        member_name = member.name if member else "該會員"

        # 查找活動與主辦人
        activity = db.query(Activity).filter_by(activity_id=activity_id).first()
        organizer_id = activity.organizer_id if activity else None

        # 只有 joined 狀態才更新 current_participants
        should_update_count = activity_join.status == "joined"
        db.delete(activity_join)
        if should_update_count and activity and activity.current_participants > 0:
            activity.current_participants -= 1

        # 新增通知給主辦人
        from app.models.notification import Notification
        if organizer_id:
            content = f"{member_name} 取消參加您的活動：{activity.title if activity else ''}"
            notification = Notification(
                member_id=organizer_id,
                title="參加者取消活動通知",
                content=content
            )
            db.add(notification)

        # 通知所有 waiting 狀態的人有名額釋出
        if activity:
            waiting_list = db.query(ActivityJoin).filter_by(activity_id=activity_id, status="waiting").all()
            for w in waiting_list:
                wait_notify = Notification(
                    member_id=w.member_id,
                    title="活動釋出名額通知",
                    content=f"您曾報名的活動「{activity.title}」有名額釋出，歡迎立即報名參加！"
                )
                db.add(wait_notify)

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

            # 預設通知內容
            notify_title = "活動審核通知"
            notify_content = ""

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
                    notify_content = f"您申請參加的活動「{activity.title}」已通過審核，歡迎參加！"

                    # 若通過後人數已達上限，處理剩餘 pending
                    if activity.current_participants >= activity.max_participants:
                        # 查詢所有還在 pending 的參加者（不含本次通過的）
                        pendings = db.query(ActivityJoin).filter(
                            ActivityJoin.activity_id == activity_id,
                            ActivityJoin.status == "pending",
                            ActivityJoin.member_id != member_id
                        ).all()
                        from app.models.notification import Notification
                        for p in pendings:
                            p.status = "waiting"
                            wait_notify = Notification(
                                member_id=p.member_id,
                                title="活動額滿通知",
                                content=f"您申請參加的活動「{activity.title}」因名額已滿，歡迎下次再度報名，有興趣請多關注本活動動態。"
                            )
                            db.add(wait_notify)
            elif new_status == "reject" and participant.status == "pending":
                activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
                if activity:
                    notify_content = f"您申請參加的活動「{activity.title}」未通過審核，請留意其他活動。"

            participant.status = new_status

            # 新增通知
            if notify_content:
                from app.models.notification import Notification
                notification = Notification(
                    member_id=member_id,
                    title=notify_title,
                    content=notify_content
                )
                db.add(notification)

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

        # 檢查是否在主辦人的黑名單中
        from app.models.blacklist import Blacklist
        blacklisted = db.query(Blacklist).filter_by(member_id=activity.organizer_id, blocked_member_id=member_id).first()
        if blacklisted:
            return jsonify({"error": "您已被主辦人加入黑名單，無法參加此活動"}), 403

        # 只有 open 或 deadline 狀態允許報名，其他狀態一律拒絕
        if activity.status not in ["open", "deadline"]:
            return jsonify({"error": "報名已截止，無法申請參加"}), 403


        if activity.current_participants >= activity.max_participants:
            return jsonify({"error": "活動已額滿"}), 403


        existing = db.query(ActivityJoin).filter_by(member_id=member_id, activity_id=activity_id).first()
        if existing:
            if existing.status == "waiting":
                existing.status = "pending"
                db.commit()
                # 仍然要通知主辦人
            else:
                return jsonify({"error": "已參加或申請過此活動"}), 409
        else:
            join = ActivityJoin(
                member_id=member_id,
                activity_id=activity_id,
                status="pending",
                has_review=False,
                is_checked_in=False
            )
            db.add(join)

        # 新增通知給主辦人
        from app.models.notification import Notification
        # 查詢申請人名稱
        member = db.query(Member).filter_by(member_id=member_id).first()
        member_name = member.name if member else "該會員"
        content = f"{member_name} 申請參加您的活動：{activity.title if activity else ''}"
        notification = Notification(
            member_id=activity.organizer_id,
            title="活動參加申請通知",
            content=content
        )
        db.add(notification)

        db.commit()

    return jsonify({"message": "申請參加成功，等待主辦人確認"}), 200

@activity_bp.route("/past_class", methods=["GET"])
def get_past_class():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
        activities = db.query(Activity).filter(Activity.type.in_(["class", "muti_class"]), Activity.organizer_id == member_id).all()
        unique_activities = {}

        for act in activities:
            key = (act.title, act.sport_type_id, act.location_name)
            if key not in unique_activities:
                unique_activities[key] = {
                    "title": act.title,
                    "sport_type_id": act.sport_type_id,
                    "location_name": act.location_name,
                    "location_lat": act.location_lat,
                    "location_lng": act.location_lng,
                }

        return jsonify(list(unique_activities.values())), 200
    
@activity_bp.route("/past_activity", methods=["GET"])
def get_past_activities():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
        activities = db.query(Activity).filter(Activity.type.in_(["activity"]), Activity.organizer_id == member_id).all()
        unique_activities = {}

        for act in activities:
            key = (act.title, act.sport_type_id, act.location_name)
            if key not in unique_activities:
                unique_activities[key] = {
                    "title": act.title,
                    "sport_type_id": act.sport_type_id,
                    "location_name": act.location_name,
                    "location_lat": act.location_lat,
                    "location_lng": act.location_lng,
                }

        return jsonify(list(unique_activities.values())), 200

@activity_bp.route("/favorite", methods=["POST"])
def add_favorite():
    try:
        data = request.get_json()
        member_id = data.get("member_id")
        activity_id = data.get("activity_id")

        if not member_id or not activity_id:
            return jsonify({"error": "缺少必要參數", "details": {"member_id": member_id, "activity_id": activity_id}}), 400

        with get_db() as db:
            # 檢查是否已存在
            existing_favorite = db.query(ActivityFavorite).filter_by(member_id=member_id, activity_id=activity_id).first()
            if existing_favorite:
                return jsonify({"error": "已收藏"}), 400

            # 新增收藏，強制設置 created_at 為 datetime.now()
            favorite = ActivityFavorite(member_id=member_id, activity_id=activity_id, created_at=datetime.now())
            db.add(favorite)
            db.commit()

        return jsonify({"message": "收藏成功"}), 201
    except Exception as e:
        return jsonify({"error": f"伺服器錯誤: {str(e)}"}), 500

@activity_bp.route("/favorite", methods=["DELETE"])
def remove_favorite():
    try:
        data = request.get_json()
        member_id = data.get("member_id")
        activity_id = data.get("activity_id")

        if not member_id or not activity_id:
            return jsonify({"error": "缺少必要參數"}), 400

        with get_db() as db:
            # 刪除收藏
            favorite = db.query(ActivityFavorite).filter_by(member_id=member_id, activity_id=activity_id).first()
            if not favorite:
                return jsonify({"error": "收藏不存在"}), 404

            db.delete(favorite)
            db.commit()

        return jsonify({"message": "移除收藏成功"}), 200
    except Exception as e:
        return jsonify({"error": f"伺服器錯誤: {str(e)}"}), 500

@activity_bp.route("/favorite/list", methods=["GET"])
def get_favorite_activities():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
        favorites = db.query(ActivityFavorite.activity_id).filter(ActivityFavorite.member_id == member_id).all()
        activity_ids = [favorite.activity_id for favorite in favorites]

    return jsonify(activity_ids), 200

@activity_bp.route("/user_activity_stats", methods=["GET"])
def get_user_activity_stats():
    member_id = request.args.get("member_id")
    if not member_id:
        return jsonify({"error": "缺少 member_id"}), 400

    with get_db() as db:
        # 查詢使用者參加的活動
        joined_activities = (
            db.query(ActivityJoin.activity_id)
            .join(Activity, ActivityJoin.activity_id == Activity.activity_id)
            .filter(ActivityJoin.member_id == member_id, ActivityJoin.status == "joined", Activity.status == "close")
            .all()
        )

        # 查詢使用者作為發起者的活動
        organized_activities = (
            db.query(Activity.activity_id)
            .filter(Activity.organizer_id == member_id, Activity.status == "close")
            .all()
        )

        # 合併活動 ID
        activity_ids = [activity.activity_id for activity in joined_activities] + [activity.activity_id for activity in organized_activities]

        if not activity_ids:
            return jsonify({"error": "該使用者未參加或發起任何已結束的活動"}), 404

        # 查詢活動詳細資訊並計算持續時間
        activities = (
            db.query(Activity)
            .filter(Activity.activity_id.in_(activity_ids))
            .all()
        )

        activity_durations = []
        sport_type_count = {}

        for activity in activities:
            if activity.start_time and activity.end_time:
                duration = (activity.end_time - activity.start_time).total_seconds() / 3600  # 持續時間（小時）
                activity_durations.append(duration)

            if activity.sport_type_id:
                sport_type = db.query(SportType).filter(SportType.sport_type_id == activity.sport_type_id).first()
                if sport_type:
                    sport_name = sport_type.name
                    if sport_name in sport_type_count:
                        sport_type_count[sport_name] += 1
                    else:
                        sport_type_count[sport_name] = 1

        # 計算最常參加的運動種類及次數
        most_common_sport = max(sport_type_count, key=sport_type_count.get) if sport_type_count else None
        most_common_sport_count = sport_type_count[most_common_sport] if most_common_sport else 0

        return jsonify({
            "total_activities": len(activity_ids),
            "total_duration_hours": sum(activity_durations),
            "most_common_sport": most_common_sport,
            "most_common_sport_count": most_common_sport_count
        }), 200
    
@activity_bp.route("/attendance", methods=["POST"])
def update_attendance():
    data = request.get_json()
    activity_id = data.get("activity_id")
    participants = data.get("participants", [])
    if not activity_id or not isinstance(participants, list):
        return jsonify({"error": "缺少必要參數"}), 400

    with get_db() as db:
        checked_in_member_ids = []
        for p in participants:
            member_id = p.get("member_id")
            is_checked_in = p.get("is_checked_in", 0)
            if not member_id:
                continue
            join = db.query(ActivityJoin).filter_by(activity_id=activity_id, member_id=member_id).first()
            if join:
                join.is_checked_in = bool(is_checked_in)
                if bool(is_checked_in):
                    checked_in_member_ids.append(member_id)
        # 發送通知給每位已簽到的參加者
        activity = db.query(Activity).filter_by(activity_id=activity_id).first()
        if activity and checked_in_member_ids:
            from app.models.notification import Notification
            for member_id in checked_in_member_ids:
                content = f"您已成功簽到活動「{activity.title}」。"
                notification = Notification(
                    member_id=member_id,
                    title="活動簽到成功通知",
                    content=content
                )
                db.add(notification)
        db.commit()
    return jsonify({"message": "點名狀態已更新，已通知簽到者"}), 200

