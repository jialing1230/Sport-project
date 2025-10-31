from sqlalchemy import Column, String, Date, DateTime, Boolean
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
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    city = Column(String(50), nullable=True, comment="縣市")
    area = Column(String(50), nullable=True, comment="鄉鎮市區")
    is_first_login = Column(Boolean, default=True, comment="是否為第一次登入")
    is_unfinish_preference = Column(Boolean, default=True, comment="是否完成偏好")
    public_intro = Column(String(500), nullable=True, comment="公開介紹")
    facebook_url = Column(String(255), nullable=True, comment="Facebook 連結")
    instagram_url = Column(String(255), nullable=True, comment="Instagram 連結")
    phone = Column(String(20), nullable=True, comment="手機號碼")
    is_subscribed = Column(Boolean, default=False, nullable=False, comment="是否訂閱")

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
  
    activity_favorites = relationship("ActivityFavorite", back_populates="member")
    comments = relationship("ActivityComment", back_populates="member", cascade="all, delete-orphan")
    blacklist_given = relationship("Blacklist", foreign_keys="Blacklist.member_id", back_populates="member")
    blacklist_received = relationship("Blacklist", foreign_keys="Blacklist.blocked_member_id", back_populates="blocked_member")
    photos = relationship("Photo", back_populates="member")
    notifications = relationship("Notification", back_populates="member")
    subscriptions = relationship("Subscription", back_populates="member")

# 避免循環引用，於檔案結尾再 import Notification
from app.models.notification import Notification
