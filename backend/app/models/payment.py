from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentProvider(str, enum.Enum):
    PAYPAL = "paypal"

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    provider = Column(String, nullable=False) # 'paypal'
    transaction_id = Column(String, index=True, nullable=True) # PaymentIntent ID or Order ID
    
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    status = Column(String, default=PaymentStatus.PENDING, index=True)
    
    plan_id = Column(String, nullable=True) # 'Pro', 'Empresa'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # User relationship can be accessed if User model has backref or we define it here if needed
    # user = relationship("User", back_populates="payments")
