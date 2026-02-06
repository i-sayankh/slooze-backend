from pydantic import BaseModel
from typing import Optional

from app.schemas.restaurant import PaginationMetadata


# Request schemas
class PaymentMethodCreate(BaseModel):
    type: str
    provider: str
    last_four: str
    is_default: bool = False


class PaymentMethodUpdate(BaseModel):
    provider: Optional[str] = None
    is_default: Optional[bool] = None


# Response schemas
class PaymentMethodResponse(BaseModel):
    id: int
    type: str
    provider: str
    last_four: str
    is_default: bool

    class Config:
        from_attributes = True


class PaymentMethodCreatedResponse(BaseModel):
    message: str
    id: int


class PaymentMethodListResponse(BaseModel):
    items: list[PaymentMethodResponse]
    pagination_metadata: PaginationMetadata


class PaymentMethodUpdatedResponse(BaseModel):
    message: str
