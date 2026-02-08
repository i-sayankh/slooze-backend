from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models import User, Role, Country
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from app.schemas.errors import (
    build_responses,
    BAD_REQUEST_400,
    UNAUTHORIZED_401,
    VALIDATION_422,
    INTERNAL_SERVER_ERROR_500,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post(
    "/register",
    response_model=RegisterResponse,
    responses=build_responses(BAD_REQUEST_400, VALIDATION_422, INTERNAL_SERVER_ERROR_500),
    summary="Register a new user",
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account and return an access token.

    **Possible errors:**
    - **400** – Invalid role or country provided.
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
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


@router.post(
    "/login",
    response_model=LoginResponse,
    responses=build_responses(UNAUTHORIZED_401, VALIDATION_422, INTERNAL_SERVER_ERROR_500),
    summary="Authenticate and get a token",
)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate with email and password.

    **Possible errors:**
    - **401** – Invalid email or password.
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
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
