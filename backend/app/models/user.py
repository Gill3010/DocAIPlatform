from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
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

    # Autenticación social
    auth_provider = Column(String, default="email")  # 'email' | 'google' | 'facebook'
    provider_user_id = Column(String, nullable=True, index=True)  # ID en el proveedor OAuth

    # Free tier usage tracking
    free_conversion_count = Column(Integer, default=0)
    ai_message_count = Column(Integer, default=0)  # Créditos usados solo en Asistente IA (límite separado)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Perfil: foto (URL tras subir imagen)
    avatar_url = Column(String, nullable=True)
