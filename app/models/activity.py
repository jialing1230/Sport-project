from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    DECIMAL,
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
    type = Column(String(50))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location_name = Column(String(255))
    location_lat = Column(DECIMAL(18, 15))
    location_lng = Column(DECIMAL(18, 15))
    max_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    min_participants = Column(Integer, nullable=False, comment="活動人數下限")
    organizer_id = Column(String(36), ForeignKey("members.member_id"))
    level = Column(String(50))
    sport_type_id = Column(Integer, ForeignKey("sport_types.sport_type_id"))
    description = Column(Text)
    status = Column(String(50))
    created_at = Column(DateTime)
    has_review = Column(Boolean)
    target_identity = Column(String(50))
    gender = Column(String(10))
    age_range = Column(String(20))
    venue_fee = Column(DECIMAL(10, 2))  
    registration_deadline = Column(DateTime)
    is_discounted = Column(Boolean, default=False, nullable=False, comment="是否參與優惠活動")
    


    # 關聯
    organizer = relationship("Member", back_populates="activities")
    sport_type = relationship("SportType", back_populates="activities")
    joins = relationship("ActivityJoin", back_populates="activity")
    reviews = relationship("ActivityReview", back_populates="activity")
    course_schedules = relationship("CourseSchedule", back_populates="activity")
    user_reviews = relationship("UserReview", back_populates="activity")
    favorites = relationship("ActivityFavorite", back_populates="activity")
