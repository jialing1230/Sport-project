from sqlalchemy import Column, Integer,  ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PreferenceSport(Base):
    __tablename__ = "preference_sport"
    preference_sport_id = Column(Integer, primary_key=True, index=True)
    preference_id = Column(Integer, ForeignKey("sport_preferences.preference_id"))
    sport_type_id = Column(Integer, ForeignKey("sport_types.sport_type_id"))

    # 關聯到 SportPreference 和 SportType
    preference = relationship("SportPreference", back_populates="sports")
    sport_type = relationship("SportType", back_populates="preference_sports")
