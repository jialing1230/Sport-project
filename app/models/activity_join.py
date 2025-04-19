from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.database import Base


class ActivityJoin(Base):
    __tablename__ = "activity_joins"
    join_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.member_id"))
    activity_id = Column(Integer, ForeignKey("activities.activity_id"))
    join_time = Column(DateTime)
    status = Column(String(50))

    member = relationship("Member", back_populates="activity_joins")
    activity = relationship("Activity", back_populates="joins")
