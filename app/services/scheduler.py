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
            # 如果活動已經是 close，則跳過更新
            if activity.status == "close":
                continue

            if activity.end_time and activity.end_time < now:
                activity.status = "close"

                # 更新 activity_join 表中此 activity_id 的 pending 狀態為 reject
                pending_participants = db.query(ActivityJoin).filter(
                    ActivityJoin.activity_id == activity.activity_id,
                    ActivityJoin.status == "pending"
                ).all()

                for participant in pending_participants:
                    participant.status = "reject"

            elif activity.start_time and activity.start_time > now:
                activity.status = "open"
            else:
                activity.status = "ongoing"
        db.commit()

def start_scheduler():
    logger.info("Starting the scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_activity_status, 'interval', minutes=1)  
    scheduler.start()