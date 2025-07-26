from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, String
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ActivityFavorite(Base):
    __tablename__ = 'activity_favorite'

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(String(36), ForeignKey('members.member_id'), nullable=False)
    activity_id = Column(Integer, ForeignKey('activities.activity_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('member_id', 'activity_id', name='uq_member_activity'),
    )
