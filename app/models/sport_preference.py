from sqlalchemy import Column, Integer, ForeignKey,String
from sqlalchemy.orm import relationship
from app.database import Base


class SportPreference(Base):
    __tablename__ = "sport_preferences"
    preference_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(36), ForeignKey("members.member_id"))
    sport_type_id = Column(Integer, ForeignKey("sport_types.sport_type_id"))

    member = relationship("Member", back_populates="sport_preferences")
    sport_type = relationship("SportType", back_populates="preferences")
