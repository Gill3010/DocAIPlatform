"""
Capa de excepciones de dominio. Prioridad 4.
Las excepciones se mapean a HTTP en un único handler en main.py.
"""
from typing import Optional


class AppException(Exception):
    """Base para excepciones de dominio. status_code y detail se usan en la respuesta HTTP."""

    def __init__(
        self,
        message: str = "Application error",
        status_code: int = 500,
        detail: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or message


# --- Auth / Credits ---
class InvalidCredentials(AppException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(message=message, status_code=401, detail=message)


class InvalidInput(AppException):
    def __init__(self, message: str = "Invalid input"):
        super().__init__(message=message, status_code=400, detail=message)


class AuthLimitReached(AppException):
    def __init__(self, message: str = "auth_limit_reached"):
        super().__init__(message=message, status_code=403, detail=message)


class AnonymousLimitReached(AppException):
    def __init__(self, message: str = "anonymous_limit_reached"):
        super().__init__(message=message, status_code=403, detail=message)


class AICreditsExhausted(AppException):
    def __init__(self, message: str = "AI credits exhausted. Please upgrade to Premium for unlimited AI assistance."):
        super().__init__(message=message, status_code=403, detail=message)


class PremiumFormatRequired(AppException):
    def __init__(self, message: str = "premium_format_required"):
        super().__init__(message=message, status_code=403, detail=message)


# --- Resources ---
class NotFound(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404, detail=message)


class Forbidden(AppException):
    def __init__(self, message: str = "Not enough permissions"):
        super().__init__(message=message, status_code=403, detail=message)


# --- User / Profile ---
class UserNotFound(NotFound):
    def __init__(self, message: str = "User not found"):
        super().__init__(message=message)


class CannotChangePasswordSocial(AppException):
    def __init__(self, message: str = "Cannot change password for social login accounts."):
        super().__init__(message=message, status_code=400, detail=message)


# --- Document ---
class DocumentNotFound(NotFound):
    def __init__(self, message: str = "Document not found"):
        super().__init__(message=message)


class OnlyOwnersCan(AppException):
    def __init__(self, message: str = "Only owners can perform this action"):
        super().__init__(message=message, status_code=403, detail=message)
