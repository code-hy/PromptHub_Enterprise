"""Auth router — login returns a token; demo mode returns the demo user."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas.api import LoginRequest, LoginResponse, UserSummary
from ..security import create_token, get_current_user, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

_shown_fields = (
    "id",
    "user_id",
    "username",
    "display_name",
    "email",
    "role",
    "department",
    "title",
)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    if user.password_hash and not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    return LoginResponse(token=create_token(user), user=_summarize(user))


@router.get("/me", response_model=UserSummary)
def me(user: User = Depends(get_current_user)):
    return _summarize(user)


def _summarize(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        department=user.department,
        title=user.title,
    )
