from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric
from app.database import Base
from datetime import datetime

class Class(Base):
    __tablename__ = "classes"

    class_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location_name = Column(String(255), nullable=False)
    location_lat = Column(Numeric(10, 6))
    location_lng = Column(Numeric(10, 6))
    max_participants = Column(Integer, nullable=False)
    venue_fee = Column(Numeric(10, 2), default=0.00)
    registration_deadline = Column(DateTime, nullable=False)
    organizer_id = Column(Integer, nullable=False)
    level = Column(String(10), nullable=False)
    sport_type_id = Column(Integer, nullable=False)
    description = Column(Text)
    status = Column(String(10), nullable=False, default="open")
    target_identity = Column(String(20), default="不限")
    gender = Column(String(10), nullable=False)
    age_range = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯 sport_type（選擇性，如果你在其他地方有定義 back_populates）
    # from app.models.sport_type import SportType
    # sport_type = relationship("SportType", back_populates="classes")
