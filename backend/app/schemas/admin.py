from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class AdminUserListItem(BaseModel):
    """Item del listado GET /admin/users."""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    can_access_admin_panel: bool
    can_view_payments: bool
    auth_provider: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminUserDetail(AdminUserListItem):
    """Detalle GET /admin/users/{id} (incluye últimas conversiones)."""
    free_conversion_count: int = 0
    ai_message_count: int = 0
    avatar_url: Optional[str] = None
    last_conversions: Optional[List[dict]] = None

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    """Body para PATCH /admin/users/{id}."""
    is_active: Optional[bool] = None
    can_access_admin_panel: Optional[bool] = None
    can_view_payments: Optional[bool] = None


class AdminUsersListResponse(BaseModel):
    """Respuesta paginada de GET /admin/users."""
    items: List[AdminUserListItem]
    total: int
    page: int
    size: int
    pages: int


class AdminConversionListItem(BaseModel):
    """Item del listado GET /admin/conversions."""
    id: int
    user_id: Optional[int] = None
    anonymous_session_id: Optional[str] = None
    original_filename: str
    original_format: str
    target_format: str
    status: str
    file_size: Optional[float] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminConversionsListResponse(BaseModel):
    """Respuesta paginada de GET /admin/conversions."""
    items: List[AdminConversionListItem]
    total: int
    page: int
    size: int
    pages: int


class AdminActivityItem(BaseModel):
    """Item del listado GET /admin/activity (audit log)."""
    id: int
    admin_user_id: int
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminActivityListResponse(BaseModel):
    """Respuesta paginada de GET /admin/activity."""
    items: List[AdminActivityItem]
    total: int
    page: int
    size: int
    pages: int


class AdminPaymentListItem(BaseModel):
    """Item del listado GET /admin/payments."""
    id: int
    user_id: int
    user_email: Optional[str] = None
    provider: str
    transaction_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    plan_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminPaymentsListResponse(BaseModel):
    """Respuesta paginada de GET /admin/payments."""
    items: List[AdminPaymentListItem]
    total: int
    page: int
    size: int
    pages: int
