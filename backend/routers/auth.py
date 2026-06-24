from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.database import get_db
from backend.db.queries import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    update_user_last_active,
)
from backend.models.orm import User
from backend.models.schemas import APIResponse, LoginRequest, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=APIResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)) -> APIResponse:
    if await get_user_by_email(db, req.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    if await get_user_by_username(db, req.username):
        raise HTTPException(status_code=409, detail="Username already taken")

    hashed = hash_password(req.password)
    user = await create_user(
        db,
        email=req.email,
        username=req.username,
        hashed_password=hashed,
    )

    token = create_access_token({"sub": str(user.id)})
    return APIResponse(
        success=True,
        message="User registered",
        data={
            "token": token,
            "expires_in": settings.access_token_expire_minutes * 60,
            "user_id": user.id,
        },
    )


@router.post("/login", response_model=APIResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)) -> APIResponse:
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await update_user_last_active(db, user.id)

    token = create_access_token({"sub": str(user.id)})
    return APIResponse(
        success=True,
        message="Login successful",
        data={
            "token": token,
            "expires_in": settings.access_token_expire_minutes * 60,
            "user_id": user.id,
        },
    )


@router.get("/me", response_model=APIResponse)
async def me(current_user: User = Depends(get_current_user)) -> APIResponse:
    return APIResponse(
        success=True,
        message="Current user",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_active": current_user.last_active.isoformat()
            if current_user.last_active
            else None,
        },
    )
