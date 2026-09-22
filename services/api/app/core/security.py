"""JWT authentication and authorization helpers.

Identity is derived exclusively from the signed token — never from client
request bodies. Endpoints that mutate records depend on `require_doctor`.
"""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(name: str, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {"sub": name, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Return ``{name, role}`` from a verified bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = _decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    return {"name": payload.get("sub"), "role": payload.get("role")}


def require_doctor(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor role required",
        )
    return user
