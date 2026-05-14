from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserLogin, Token
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=UserSchema)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    # Create new user
    db_obj = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        preferred_language=user_in.preferred_language
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(deps.get_db)
):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()
    
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
