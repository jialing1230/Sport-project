from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class SportPreference(Base):
    __tablename__ = "sport_preferences"
    preference_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(36), ForeignKey("members.member_id"))
    match_gender = Column(String(10))  # 性別偏好
    match_age = Column(String(20))  # 年齡偏好

    member = relationship("Member", back_populates="sport_preferences")

    # 新增關聯：一個運動偏好有多個運動類型
    sports = relationship("PreferenceSport", back_populates="preference")
    times = relationship("PreferenceTime", back_populates="preference")
