from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class PreferenceTime(Base):
    __tablename__ = "preference_time"

    # 使用複合主鍵：preference_id 和 time_id
    preference_id = Column(Integer, ForeignKey("sport_preferences.preference_id"), primary_key=True)
    time_id = Column(Integer, ForeignKey("time_option.time_id"), primary_key=True)

    # 關聯到 SportPreference 和 TimeOption
    preference = relationship("SportPreference", back_populates="times")
    time_option = relationship("TimeOption", back_populates="preference_times")

    # 設置唯一約束
    __table_args__ = (
        UniqueConstraint('preference_id', 'time_id', name='uq_preference_time_id'),
    )
