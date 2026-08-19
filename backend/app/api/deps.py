"""API dependencies — shared auth / db helpers."""

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import get_current_user, require_role

__all__ = ["Session", "User", "get_current_user", "get_db", "require_role"]
