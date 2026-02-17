from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)  # Nullable para usuarios solo-social
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    can_access_admin_panel = Column(Boolean, default=False)
    can_view_payments = Column(Boolean, default=False)

    # Autenticación social
    auth_provider = Column(String, default="email")  # 'email' | 'google' | 'facebook'
    provider_user_id = Column(String, nullable=True, index=True)  # ID en el proveedor OAuth

    # Verificación de email (NULL = no verificado; datetime = verificado)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Free tier usage tracking
    free_conversion_count = Column(Integer, default=0)
    ai_message_count = Column(Integer, default=0)  # Créditos usados solo en Asistente IA (límite separado)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Perfil: foto (URL tras subir imagen)
    avatar_url = Column(String, nullable=True)

    # Premium / Payment integration
    is_premium = Column(Boolean, default=False)
    premium_plan_id = Column(String, nullable=True)  # e.g. 'Básico', 'Pro', 'Empresa'
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    paypal_payer_id = Column(String, nullable=True)

    # Monthly limits tracking
    monthly_conversion_count = Column(Integer, default=0)
    last_billing_reset = Column(DateTime(timezone=True), nullable=True)

    # Multi-usuario (Empresa)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="members", foreign_keys=[organization_id])
