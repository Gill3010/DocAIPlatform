from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    original_format = Column(String)
    content = Column(LargeBinary, nullable=True)  # Binary data for Yjs state
    initial_content = Column(Text, nullable=True) # Text or HTML for first load
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", backref="documents")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")

class DocumentPermission(Base):
    __tablename__ = "document_permissions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # 'viewer', 'editor'
    
    document = relationship("Document", back_populates="permissions")
    user = relationship("User")
