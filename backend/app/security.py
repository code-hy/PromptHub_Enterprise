"""Lightweight auth: PBKDF2 password hashing, HMAC-signed tokens, demo user.

Auth is optional by default (ENABLE_AUTH=false). When disabled, every request
acts as the seeded demo user ("Henry") so the demo works with zero setup.
"""

import hashlib
import hmac
import os
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, get_db
from .models import User


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _scheme, salt_hex, derived_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    expected = hash_password(password, salt)
    return hmac.compare_digest(expected, stored)


def create_token(user: User) -> str:
    payload = f"{user.user_id}:{user.id}:{user.role}:{datetime.now(UTC).timestamp()}"
    signature = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def decode_token(token: str) -> dict | None:
    try:
        payload, signature = token.rsplit(".", 1)
        expected = hmac.new(
            settings.secret_key.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return None
        user_id, db_id, role, ts = payload.split(":")
        age = datetime.now(UTC).timestamp() - float(ts)
        if age > settings.access_token_expire_minutes * 60:
            return None
        return {"user_id": user_id, "id": int(db_id), "role": role}
    except (ValueError, AttributeError):
        return None


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Return the demo user when auth is disabled, else the bearer identity."""
    if not settings.enable_auth:
        return demo_user(db)
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    claims = decode_token(credentials.credentials)
    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, claims["id"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*roles: str):
    def wrapper(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return wrapper


def demo_user(db: Session | None = None) -> User:
    """The default logged-in user when auth is disabled."""
    if db is None:
        with SessionLocal() as session:
            return _demo(session)
    return _demo(db)


def _demo(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == "henry"))
    if user is None:
        user = db.scalar(select(User).order_by(User.id).limit(1))
    if user is None:
        raise HTTPException(status_code=500, detail="No users in database — run seed")
    return user
