from sqlalchemy import Column, Integer, ForeignKey, String, Float, Date, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ExerciseRecord(Base):
    __tablename__ = "exercise_records"
    record_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.member_id"))
    sport_type_id = Column(Integer, ForeignKey("sport_types.sport_type_id"))
    location = Column(String(255))
    location_lat = Column(Float)
    location_lng = Column(Float)
    duration_hours = Column(Float)
    record_date = Column(Date)
    intensity_level = Column(String(50))
    notes = Column(Text)

    member = relationship("Member", back_populates="exercise_records")
    sport_type = relationship("SportType", back_populates="exercise_records")
