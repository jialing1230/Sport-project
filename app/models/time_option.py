from sqlalchemy import Column, Integer, String
from app.database import Base

class TimeOption(Base):
    __tablename__ = "time_option"

    time_id = Column(Integer, primary_key=True, autoincrement=True)  # 主鍵
    period = Column(String(50), nullable=False)  # 平日或周末
    time_of_day = Column(String(50), nullable=False)  # 早上、中午或晚上
    label = Column(String(100), nullable=False)  # 時間描述組合

    def __repr__(self):
        return f"<TimeOption(period={self.period}, time_of_day={self.time_of_day}, label={self.label})>"
