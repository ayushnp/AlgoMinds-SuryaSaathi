from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt

from core.config import settings

# ============================================================
# PASSWORD HASHING CONTEXT (Argon2 – modern, secure, no limits)
# ============================================================
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 password token scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


# ============================================================
# PASSWORD HASHING + VERIFICATION (simple, secure)
# ============================================================

def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.
    Argon2 has NO 72-byte limit like bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password using Argon2.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# JWT TOKEN CREATION + EXTRACTION
# ============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()

    # Ensure 'sub' is a string
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_user_id_from_token(token: str) -> str:
    """Extracts user_id (sub) from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


# ============================================================
# FASTAPI DEPENDENCY FOR PROTECTED ROUTES
# ============================================================

async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> str:
    """Dependency for protected routes that returns user_id from JWT."""
    return get_user_id_from_token(token)
