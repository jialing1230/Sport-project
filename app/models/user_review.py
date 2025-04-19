from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class UserReview(Base):
    __tablename__ = "user_reviews"
    review_id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("members.member_id"))
    target_member_id = Column(Integer, ForeignKey("members.member_id"))
    rating = Column(Integer)
    comment = Column(Text)
    created_time = Column(DateTime)

    reviewer = relationship(
        "Member", foreign_keys=[reviewer_id], back_populates="user_reviews_given"
    )
    target_member = relationship(
        "Member",
        foreign_keys=[target_member_id],
        back_populates="user_reviews_received",
    )
