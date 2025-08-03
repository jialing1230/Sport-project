from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Blacklist(Base):
    __tablename__ = 'blacklist'

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(36), ForeignKey('members.member_id'), nullable=False)
    blocked_member_id = Column(String(36), ForeignKey('members.member_id'), nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship('Member', foreign_keys=[member_id])
    blocked_member = relationship('Member', foreign_keys=[blocked_member_id])
