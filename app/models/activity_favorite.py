from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, String
from app.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class ActivityFavorite(Base):
    __tablename__ = 'activity_favorite'

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(String(36), ForeignKey('members.member_id'), nullable=False)
    activity_id = Column(Integer, ForeignKey('activities.activity_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('member_id', 'activity_id', name='uq_member_activity'),
    )

    member = relationship("Member", back_populates="activity_favorites")
    activity = relationship("Activity", back_populates="favorites")
