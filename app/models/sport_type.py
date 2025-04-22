from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class SportType(Base):
    __tablename__ = "sport_types"
    sport_type_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    activities = relationship("Activity", back_populates="sport_type")
    exercise_records = relationship("ExerciseRecord", back_populates="sport_type")
    preference_sports = relationship("PreferenceSport", back_populates="sport_type")
