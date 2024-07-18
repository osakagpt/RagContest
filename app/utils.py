from datetime import timedelta, datetime, timezone
from typing import List, Dict, Optional

from fastapi import Request, Depends, HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import jwt_settings
from database import get_db_session
from model import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def format_millisec(milliseconds: int) -> str:
    # Convert milliseconds to seconds and microseconds
    seconds, millis = divmod(milliseconds, 1000)
    # Create a timedelta object
    delta = timedelta(seconds=seconds, milliseconds=millis)
    # Extract hours, minutes, and seconds from the timedelta object
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Format the time string
    time_string = f"{hours:02}:{minutes:02}:{seconds:02}.{delta.microseconds // 1000:03}"
    return time_string


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, jwt_settings.SECRET_KEY, algorithm=jwt_settings.ALGORITHM)
    return encoded_jwt


def fetch_access_token_from_cookie_header(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is missing")
    return access_token


# Example function to authenticate user and generate access token
async def authenticate_user(
    email: str, password: str, session: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    result = await session.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user
