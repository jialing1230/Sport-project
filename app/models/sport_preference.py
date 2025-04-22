from sqlalchemy import Column, Integer, ForeignKey,String
from sqlalchemy.orm import relationship
from app.database import Base


class SportPreference(Base):
    __tablename__ = "sport_preferences"
    preference_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(36), ForeignKey("members.member_id"))
    match_gender = Column(String(10))  # 限制或不限性別
    match_age = Column(String(20))

    member = relationship("Member", back_populates="sport_preferences")
    
