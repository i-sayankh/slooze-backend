from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models import User, Role, Country
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/register", response_model=RegisterResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):

    role = await db.scalar(select(Role).where(Role.name == data.role.value))
    country = await db.scalar(select(Country).where(Country.name == data.country.value))

    if not role or not country:
        raise HTTPException(status_code=400, detail="Invalid role or country")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=role.id,
        country_id=country.id,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "name": user.name,
        "email": user.email,
    })
    return RegisterResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        access_token=token,
    )


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):

    user = await db.scalar(
        select(User).where(User.email == data.email).options(selectinload(User.role))
    )

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role.name,
    })
    return LoginResponse(access_token=token)
