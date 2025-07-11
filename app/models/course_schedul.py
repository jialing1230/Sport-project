from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship



class CourseSchedule(Base):
    __tablename__ = "course_schedule"

    course_schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey("activity.activity_id"), nullable=False)
    session_number = Column(Integer, nullable=False)
    weekday = Column(String(10), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    activity = relationship("Activity", back_populates="Activity")
