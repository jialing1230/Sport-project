from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class ActivityComment(Base):
    __tablename__ = "activity_comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.activity_id", ondelete="CASCADE"))
    member_id = Column(String(36), ForeignKey("members.member_id", ondelete="CASCADE"))
    parent_id = Column(Integer, ForeignKey("activity_comments.comment_id"), nullable=True, comment="回覆留言ID")

    content = Column(Text, nullable=False, comment="留言內容")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False, comment="是否已刪除")
    is_pinned = Column(Boolean, default=False, comment="是否置頂（例如主辦人公告）")

    # 關聯
    activity = relationship("Activity", back_populates="comments")
    member = relationship("Member", back_populates="comments")
    replies = relationship("ActivityComment", backref="parent", remote_side=[comment_id])
