import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Annotated

from app.database.session import get_db
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse

users_router = APIRouter(prefix="/users", tags=["Users"])

DBDep = Annotated[AsyncSession, Depends(get_db)]

@users_router.post(
    "/register",
    summary="User registration",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(user_in: UserCreate, session: DBDep):
    """Регистрация нового пользователя"""
    
    hashed_key = hashlib.sha256(user_in.api_key.encode()).hexdigest()
    new_user = User(email=user_in.email, api_key_hash=hashed_key)
    
    session.add(new_user)
    
    try:
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
        
    return new_user