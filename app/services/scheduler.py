from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.database import get_db
from app.models.activity import Activity
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
            elif activity.start_time and activity.start_time > now:
                activity.status = "open"
            else:
                activity.status = "ongoing"
        db.commit()

def start_scheduler():
    logger.info("Starting the scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_activity_status, 'interval', minutes=1)  # 每5分鐘執行一次
    scheduler.start()