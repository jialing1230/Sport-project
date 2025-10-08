from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime,timedelta
from app.database import get_db
from app.models.member import Member
from app.models.activity import Activity
from app.models.activity_join import ActivityJoin
from app.models.notification import Notification
from app.models.activity_favorite import ActivityFavorite
from app.models.course_schedul import CourseSchedule
import logging
from gmail_eval import send_eval_mail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DOMAIN = "http://ec2-52-195-207-234.ap-northeast-1.compute.amazonaws.com:8000"

def update_activity_status():
    with get_db() as db:
        now = datetime.now()
        activities = db.query(Activity).all()
        for activity in activities:
            # 按 open -> deadline -> ongoing -> close 順序更新狀態
            if activity.registration_deadline and now < activity.registration_deadline:
                if activity.status != "cancelled":
                    activity.status = "open"
            elif activity.registration_deadline and now >= activity.registration_deadline and (not activity.start_time or now < activity.start_time):
                if activity.status != "cancelled":
                    pending_participants = db.query(ActivityJoin).filter(
                        ActivityJoin.activity_id == activity.activity_id,
                        ActivityJoin.status == "pending"
                    ).all()
                    for participant in pending_participants:
                        db.delete(participant)
                    # 報名截止時檢查人數是否達下限（直接用 current_participants）
                    if getattr(activity, "current_participants", 0) >= getattr(activity, "min_participants", 0):
                        activity.status = "deadline"
                    else:
                        activity.status = "cancelled"
                        # 發起人通知
                        if activity.organizer_id:
                            notify = Notification(
                                member_id=activity.organizer_id,
                                title="活動取消通知",
                                content=f"您的活動「{activity.title}」因人數不足已取消。",
                                url=f"/api/activities/details_page?id={activity.activity_id}&member_id={activity.organizer_id}"
                            )
                            db.add(notify)
                        # 所有已報名參加者通知
                        participants = db.query(ActivityJoin).filter_by(activity_id=activity.activity_id, status="joined").all()
                        for participant in participants:
                            notify = Notification(
                                member_id=participant.member_id,
                                title="活動取消通知",
                                content=f"您參加的活動「{activity.title}」因人數不足已取消。",
                                url=f"/api/activities/details_page?id={activity.activity_id}&member_id={participant.member_id}"
                            )
                            db.add(notify)
            elif activity.start_time and now >= activity.start_time and (not activity.end_time or now < activity.end_time):
                if activity.status != "cancelled":
                    # 進行前先判斷人數是否達下限
                    if getattr(activity, "current_participants", 0) >= getattr(activity, "min_participants", 0):
                        activity.status = "ongoing"
                        pending_participants = db.query(ActivityJoin).filter(
                            ActivityJoin.activity_id == activity.activity_id,
                            ActivityJoin.status == "pending"
                        ).all()
                        for participant in pending_participants:
                            db.delete(participant)
                    else:
                        activity.status = "cancelled"
                        # 發起人通知
                        if activity.organizer_id:
                            notify = Notification(
                                member_id=activity.organizer_id,
                                title="活動取消通知",
                                content=f"您的活動「{activity.title}」因人數不足已取消。",
                                url=f"/api/activities/details_page?id={activity.activity_id}&member_id={activity.organizer_id}"
                            )
                            db.add(notify)
                        # 所有已報名參加者通知
                        participants = db.query(ActivityJoin).filter_by(activity_id=activity.activity_id, status="joined").all()
                        for participant in participants:
                            notify = Notification(
                                member_id=participant.member_id,
                                title="活動取消通知",
                                content=f"您參加的活動「{activity.title}」因人數不足已取消。",
                                url=f"/api/activities/details_page?id={activity.activity_id}&member_id={participant.member_id}"
                            )
                            db.add(notify)
            elif activity.end_time and now >= activity.end_time:
                # 結束時也判斷人數是否達下限
                if getattr(activity, "current_participants", 0) < getattr(activity, "min_participants", 0):
                    activity.status = "cancelled"
                    # 活動已取消且已結束，刪除所有相關紀錄
                    db.query(ActivityFavorite).filter_by(activity_id=activity.activity_id).delete()
                    db.query(ActivityJoin).filter_by(activity_id=activity.activity_id).delete()
                    db.query(CourseSchedule).filter_by(activity_id=activity.activity_id).delete()
                    db.query(Activity).filter_by(activity_id=activity.activity_id).delete()
                elif activity.status == "cancelled":
                    # 活動已取消且已結束，刪除所有相關紀錄
                    db.query(ActivityFavorite).filter_by(activity_id=activity.activity_id).delete()
                    db.query(ActivityJoin).filter_by(activity_id=activity.activity_id).delete()
                    db.query(CourseSchedule).filter_by(activity_id=activity.activity_id).delete()
                    db.query(Activity).filter_by(activity_id=activity.activity_id).delete()
                elif activity.status != "cancelled":
                    # 只在狀態從非 close → close 時才觸發
                    if activity.status != "close":
                        activity.status = "close"

                        # 找出所有已參加者
                        participants = db.query(ActivityJoin).filter_by(
                            activity_id=activity.activity_id,
                            status="joined"
                        ).all()

                        for participant in participants:
                            eval_link = f"{DOMAIN.rstrip('/')}/evaluate?activity_id={activity.activity_id}&member_id={participant.member_id}"

                            # 避免重複寄送，檢查是否已有通知紀錄
                            exists = db.query(Notification).filter_by(
                                member_id=participant.member_id,
                                title="活動評價邀請",
                                url=eval_link
                            ).first()

                            if not exists:
                                # 透過 member_id 查詢 email
                                member = db.query(Member).filter_by(member_id=participant.member_id).first()
                                if member and member.email and not member.email.endswith("@example.com"):
                                    try:
                                        send_eval_mail(
                                            to_email=member.email,
                                            activity_title=activity.title,
                                            eval_link=eval_link
                                        )
                                    except Exception as e:
                                        logger.error(f"寄送評價信失敗: {e}")
                                # 無論有沒有寄信都建立通知紀錄
                                notify = Notification(
                                    member_id=participant.member_id,
                                    title="活動評價邀請",
                                    content=f"感謝您參加「{activity.title}」，請留下您的評價！",
                                    url=eval_link
                                )
                                db.add(notify)

                    else:
                        activity.status = "close"
            else:
                if activity.status != "cancelled":
                    activity.status = "unknown"

        db.commit()
    
def notify_upcoming_activities():
    with get_db() as db:
        now = datetime.now()
        # 查詢2小時後即將開始的活動
        upcoming_activities = db.query(Activity).filter(
            Activity.start_time.isnot(None),
            Activity.status.in_(["open", "deadline"]),
            Activity.start_time > now,
            Activity.start_time <= now.replace(microsecond=0) + timedelta(hours=2)
        ).all()
        for activity in upcoming_activities:
            # 找出所有 joined 參加者
            participants = db.query(ActivityJoin).filter_by(activity_id=activity.activity_id, status="joined").all()
            for participant in participants:
                joined_url = f"/api/activities/joined_details_page?id={activity.activity_id}&member_id={participant.member_id}"
                # 檢查是否已發送過同樣通知
                exists = db.query(Notification).filter_by(
                    member_id=participant.member_id,
                    title="活動即將開始提醒",
                    url=joined_url
                ).first()
                if not exists:
                    notify = Notification(
                        member_id=participant.member_id,
                        title="活動即將開始提醒",
                        content=f"您參加的活動「{activity.title}」將於兩小時後開始，請記得準時參加並向發起人簽到！",
                        url=joined_url
                    )
                    db.add(notify)
        db.commit()

def start_scheduler():
    logger.info("Starting the scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_activity_status, 'interval', minutes=1)
    scheduler.add_job(notify_upcoming_activities, 'interval', minutes=3)
    scheduler.start()