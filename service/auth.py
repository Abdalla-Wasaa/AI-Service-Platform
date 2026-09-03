"""JWT authentication and role-based authorization."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Callable

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from service.config import get_settings
from service.models import LoginRequest, TokenResponse

# Demo-only accounts. Production deployments should use an identity provider/database.
USERS = {
    "clinician": {
        "password_hash": b"$2b$12$5f1vca4sjOAs9Yd4EJ9jwur312kSE/pbf8D7roxGnjw/iXfbfAZ4.",
        "role": "clinician",
    },
    "coordinator": {
        "password_hash": b"$2b$12$noN8clhbE8PKqkOABflc3Ow666jGri96UGD53JjQNH7U4rvGZnAZK",
        "role": "coordinator",
    },
}

bearer = HTTPBearer(auto_error=False)


def authenticate(login: LoginRequest) -> TokenResponse:
    user = USERS.get(login.username)
    valid = bool(user) and bcrypt.checkpw(
        login.password.encode("utf-8"), user["password_hash"]
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.access_token_minutes)
    token = jwt.encode(
        {
            "sub": login.username,
            "role": user["role"],
            "iat": now,
            "exp": expires,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_minutes * 60,
    )


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, str]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_settings().jwt_secret,
            algorithms=["HS256"],
        )
        subject = payload.get("sub")
        role = payload.get("role")
        if not subject or role not in {"clinician", "coordinator"}:
            raise jwt.InvalidTokenError("missing claims")
        return {"sub": subject, "role": role}
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_roles(*roles: str) -> Callable:
    def dependency(user: Annotated[dict[str, str], Depends(current_user)]) -> dict[str, str]:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(roles)}",
            )
        return user

    return dependency

