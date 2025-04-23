from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Member(Base):
    __tablename__ = "members"
    member_id = Column(String(36), primary_key=True, index=True, autoincrement=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(100))
    gender = Column(String(10))
    birthdate = Column(Date)
    height = Column(Integer)
    weight = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    city = Column(String(50), nullable=True, comment="縣市")
    area = Column(String(50), nullable=True, comment="鄉鎮市區")
    avatar_url = Column(String(255), nullable=True, comment="頭像檔案路徑")
    is_first_login = Column(Boolean, default=True, comment="是否為第一次登入")

    sport_preferences = relationship("SportPreference", back_populates="member")
    activities = relationship("Activity", back_populates="organizer")
    activity_joins = relationship("ActivityJoin", back_populates="member")
    activity_reviews = relationship("ActivityReview", back_populates="reviewer")
    user_reviews_given = relationship(
        "UserReview", foreign_keys="UserReview.reviewer_id", back_populates="reviewer"
    )
    user_reviews_received = relationship(
        "UserReview",
        foreign_keys="UserReview.target_member_id",
        back_populates="target_member",
    )
    exercise_records = relationship("ExerciseRecord", back_populates="member")
