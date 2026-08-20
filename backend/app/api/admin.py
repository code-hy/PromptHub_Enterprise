"""Administration API — users and roles (spec 50)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..ids import next_user_id
from ..models import User
from ..schemas.api import UserSummary
from ..security import hash_password, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreate(BaseModel):
    username: str
    display_name: str
    email: str = ""
    department: str = ""
    title: str = ""
    role: str = "USER"
    password: str = ""


class UserUpdate(BaseModel):
    display_name: str | None = None
    email: str | None = None
    role: str | None = None
    department: str | None = None
    title: str | None = None
    is_active: bool | None = None
    password: str | None = None


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
        is_active=user.is_active,
    )


@router.get("/users", response_model=list[UserSummary])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    users = db.scalars(select(User).order_by(User.username)).all()
    return [_summarize(u) for u in users]


@router.post("/users", response_model=UserSummary)
def create_user(
    data: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))
):
    exists = db.scalar(select(User).where(User.username == data.username))
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        user_id=next_user_id(db),
        username=data.username,
        display_name=data.display_name,
        email=data.email,
        department=data.department,
        title=data.title,
        role=data.role,
        password_hash=hash_password(data.password) if data.password else "",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _summarize(user)


@router.put("/users/{user_id}", response_model=UserSummary)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    updates = data.model_dump(exclude_unset=True)
    password = updates.pop("password", None)
    for key, value in updates.items():
        setattr(user, key, value)
    if password:
        user.password_hash = hash_password(password)
    db.commit()
    db.refresh(user)
    return _summarize(user)


@router.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role("ADMIN")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    # Prevent removing the last admin so there is always an admin account
    if user.role == "ADMIN":
        admin_count = db.scalar(
            select(func.count()).select_from(User).where(User.role == "ADMIN")
        )
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin account")
    db.delete(user)
    db.commit()
    return {"ok": True}
