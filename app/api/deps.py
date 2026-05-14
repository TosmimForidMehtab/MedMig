from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import SessionLocal
from app.models.user import User
from app.config import settings
from app.schemas.user import TokenData

bearer_scheme = HTTPBearer()

async def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        await db.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.email == token_data.email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user
