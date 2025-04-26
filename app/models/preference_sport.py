from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class PreferenceSport(Base):
    __tablename__ = "preference_sport"

    # 使用複合主鍵：preference_id 和 sport_type_id
    preference_id = Column(
        Integer, ForeignKey("sport_preferences.preference_id"), primary_key=True
    )
    sport_type_id = Column(
        Integer, ForeignKey("sport_types.sport_type_id"), primary_key=True
    )

    # 關聯到 SportPreference 和 SportType
    preference = relationship("SportPreference", back_populates="sports")
    sport_type = relationship("SportType", back_populates="preference_sports")

    # 設置唯一約束
    __table_args__ = (
        UniqueConstraint(
            "preference_id", "sport_type_id", name="uq_preference_sport_id"
        ),
    )
