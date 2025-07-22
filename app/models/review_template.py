from sqlalchemy import Column, Integer, String
from app.database import Base

class ReviewTemplate(Base):
    __tablename__ = "review_templates"

    template_id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    text = Column(String(255), nullable=False)
