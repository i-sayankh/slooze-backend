from enum import Enum

from pydantic import BaseModel, EmailStr


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"


class CountryEnum(str, Enum):
    INDIA = "India"
    AMERICA = "America"


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum
    country: CountryEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
