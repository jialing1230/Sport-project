from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(36), ForeignKey("members.member_id"), nullable=False, index=True)
    subscribed_at = Column(DateTime, nullable=False)
    expire_at = Column(DateTime, nullable=True, comment="到期日")
    plan = Column(String(50), nullable=True, comment="訂閱方案")
    amount = Column(Integer, nullable=True, comment="收取金額")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否有效訂閱")

    member = relationship("Member", back_populates="subscriptions")
