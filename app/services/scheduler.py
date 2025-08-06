from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.database import get_db
from app.models.activity import Activity
from app.models.activity_join import ActivityJoin
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

def start_scheduler():
    logger.info("Starting the scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_activity_status, 'interval', minutes=1)  
    scheduler.start()