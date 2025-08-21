from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime,timedelta
from app.database import get_db
from app.models.activity import Activity
from app.models.activity_join import ActivityJoin
from app.models.notification import Notification
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_activity_status():
    with get_db() as db:
        now = datetime.now()
        activities = db.query(Activity).all()
        for activity in activities:
            # 按 open -> deadline -> ongoing -> close 順序更新狀態
            if activity.registration_deadline and now < activity.registration_deadline:
                activity.status = "open"
            elif activity.registration_deadline and now >= activity.registration_deadline and (not activity.start_time or now < activity.start_time):
                activity.status = "deadline"
                pending_participants = db.query(ActivityJoin).filter(
                    ActivityJoin.activity_id == activity.activity_id,
                    ActivityJoin.status == "pending"
                ).all()
                for participant in pending_participants:
                    db.delete(participant)
            elif activity.start_time and now >= activity.start_time and (not activity.end_time or now < activity.end_time):
                activity.status = "ongoing"
                pending_participants = db.query(ActivityJoin).filter(
                    ActivityJoin.activity_id == activity.activity_id,
                    ActivityJoin.status == "pending"
                ).all()
                for participant in pending_participants:
                    db.delete(participant)
            elif activity.end_time and now >= activity.end_time:
                activity.status = "close"
                pending_participants = db.query(ActivityJoin).filter(
                    ActivityJoin.activity_id == activity.activity_id,
                    ActivityJoin.status == "pending"
                ).all()
                for participant in pending_participants:
                    db.delete(participant)
            else:
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