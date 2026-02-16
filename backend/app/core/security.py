from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# bcrypt has a 72-byte limit; truncate to avoid ValueError
BCRYPT_MAX_PASSWORD_BYTES = 72

def _truncate_password_for_bcrypt(password: str) -> str:
    """Truncate password to 72 bytes for bcrypt (passlib requirement)."""
    encoded = password.encode("utf-8")
    if len(encoded) <= BCRYPT_MAX_PASSWORD_BYTES:
        return password
    return encoded[:BCRYPT_MAX_PASSWORD_BYTES].decode("utf-8", errors="ignore")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_truncate_password_for_bcrypt(plain_password), hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(_truncate_password_for_bcrypt(password))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token with expiration.
    
    Args:
        data: Dictionary with claims to encode (e.g., {"sub": email})
        expires_delta: Optional custom expiration time. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session (injected by FastAPI)
    
    Returns:
        User: Authenticated user object
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Query user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Returns the current user if token is valid, else None.
    For routes that support both authenticated and anonymous users.
    
    Args:
        token: Optional JWT token from Authorization header
        db: Database session (injected by FastAPI)
    
    Returns:
        User or None: Authenticated user if token is valid, None otherwise
    """
    if token is None:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
    except JWTError:
        return None
    
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _is_admin(user: User) -> bool:
    """
    Check if user has admin access (superuser or admin panel access).
    
    Args:
        user: User object to check
    
    Returns:
        bool: True if user is admin, False otherwise
    """
    # Superuser always has admin access
    if user.is_superuser:
        return True
    
    # Check if user is in SUPERADMIN_EMAILS list
    superadmin_emails = settings.SUPERADMIN_EMAILS or ""
    if superadmin_emails:
        admin_email_list = [e.strip() for e in superadmin_emails.split(",") if e.strip()]
        if user.email in admin_email_list:
            return True
    
    # Check explicit admin panel access flag
    if user.can_access_admin_panel:
        return True
    
    return False


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that requires the user to be an admin (superuser or admin panel access).
    Use in all routes under /api/v1/admin.
    
    Args:
        current_user: Current authenticated user (injected by FastAPI)
    
    Returns:
        User: Admin user object
    
    Raises:
        HTTPException: 403 if user is not admin
    """
    if not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_payment_viewer(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that requires the user to have payment viewing permissions.
    Only superadmins or users with explicit can_view_payments flag can access.
    """
    is_super = current_user.is_superuser
    # Also check settings for superadmin emails if is_superuser isn't set
    if not is_super and settings.SUPERADMIN_EMAILS:
        admin_email_list = [e.strip() for e in settings.SUPERADMIN_EMAILS.split(",") if e.strip()]
        if current_user.email in admin_email_list:
            is_super = True

    if not is_super and not getattr(current_user, "can_view_payments", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view payments.",
        )
    return current_user
