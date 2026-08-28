from sqlalchemy import Column, DateTime, Integer, Text, func
from pgvector.sqlalchemy import Vector

from app.db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(Text, nullable=False, index=True)
    file_type = Column(Text, nullable=False)
    document_hash = Column(Text, nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_char_count = Column(Integer, nullable=False)
    loaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
