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
            if activity.end_time and activity.end_time < now:
                activity.status = "close"

                # 更新 activity_join 表中此 activity_id 的 pending 狀態為 reject
                pending_participants = db.query(ActivityJoin).filter(
                    ActivityJoin.activity_id == activity.activity_id,
                    ActivityJoin.status == "pending"
                ).all()

                for participant in pending_participants:
                    participant.status = "reject"

            elif activity.registration_deadline and activity.registration_deadline < now:
                activity.status = "deadline"

            elif activity.start_time and activity.start_time > now:
                activity.status = "open"

            elif activity.start_time and activity.end_time and activity.start_time <= now <= activity.end_time:
                activity.status = "ongoing"

            else:
                activity.status = "unknown"  # 如果沒有符合條件，設置為未知狀態

        db.commit()

def start_scheduler():
    logger.info("Starting the scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_activity_status, 'interval', minutes=1)  
    scheduler.start()