from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(36), ForeignKey('members.member_id'), nullable=False)
    title = Column(String(128), nullable=False, comment='通知標題')
    content = Column(Text, nullable=False, comment='通知內容')
    is_read = Column(Boolean, default=False, nullable=False, comment='是否已讀')
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship('Member', foreign_keys=[member_id])
