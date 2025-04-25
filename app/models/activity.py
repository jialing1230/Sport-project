from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Activity(Base):
    __tablename__ = "activities"
    activity_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    time = Column(DateTime)
    location_name = Column(String(255))
    location_lat = Column(Float)
    location_lng = Column(Float)
    max_participants = Column(Integer)
    min_age = Column(Integer, nullable=True)           # 最低年齡限制（新增）
    max_age = Column(Integer, nullable=True)           # 最高年齡限制（新增）
    organizer_id = Column(String(36), ForeignKey("members.member_id"))
    level = Column(String(50))
    sport_type_id = Column(Integer, ForeignKey("sport_types.sport_type_id"))
    description = Column(Text)
    status = Column(String(50))
    created_at = Column(DateTime)
    has_review = Column(Boolean)

    organizer = relationship("Member", back_populates="activities")
    sport_type = relationship("SportType", back_populates="activities")
    joins = relationship("ActivityJoin", back_populates="activity")
    reviews = relationship("ActivityReview", back_populates="activity")
