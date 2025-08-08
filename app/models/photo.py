from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Photo(Base):
    __tablename__ = 'photo'

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(255), nullable=False)
    member_id = Column(String(36), ForeignKey('members.member_id'), nullable=False)

    member = relationship('Member', back_populates='photos')
