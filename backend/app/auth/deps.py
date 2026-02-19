"""Auth dependencies: get current user from JWT."""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.db.models import User
from app.db.session import get_session

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UUID | None:
    if not credentials or not credentials.credentials:
        return None
    sub = decode_access_token(credentials.credentials)
    if not sub:
        return None
    try:
        return UUID(sub)
    except ValueError:
        return None


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    user_id: UUID | None = Depends(get_current_user_id),
) -> User:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_optional(
    session: AsyncSession = Depends(get_session),
    user_id: UUID | None = Depends(get_current_user_id),
) -> User | None:
    if user_id is None:
        return None
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
