from sqlalchemy import Column, Integer, Text
from pgvector.sqlalchemy import Vector

from app.db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
