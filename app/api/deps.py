"""
FastAPI Route Dependencies
Provides database session, user authentication via JWT bearer tokens / cookies,
and role-based authorization guards (e.g. require_role("admin")).
"""
from typing import Generator, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, MLModel
from app.security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    bearer: HTTPAuthorizationCredentials = Depends(security_bearer)
) -> User:
    """
    Extracts and authenticates user from Authorization Bearer header or access_token cookie.
    Raises 401 if missing or invalid.
    """
    token = None
    if bearer and bearer.credentials:
        token = bearer.credentials
    else:
        # Check cookie or query param as fallback for browser navigation / downloads
        token = request.cookies.get("access_token")
        if not token:
            token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Strip 'Bearer ' if token came from cookie with prefix
    if token.startswith("Bearer "):
        token = token[7:]

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token does not exist.",
        )

    return user


def require_role(*allowed_roles: str) -> Callable[[User], User]:
    """
    Dependency factory enforcing role-based access control (RBAC).
    Raises 403 Forbidden if current user role is not in allowed_roles (TC-20).
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, but your role is '{current_user.role}'.",
            )
        return current_user
    return role_checker


def get_active_model_name(db: Session = Depends(get_db)) -> str:
    """Returns the name of the active model from the models table."""
    active_model = db.query(MLModel).filter(MLModel.status == "active").first()
    if active_model:
        return active_model.name
    return "Decision Tree"
