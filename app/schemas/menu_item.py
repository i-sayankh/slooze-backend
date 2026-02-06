from pydantic import BaseModel
from typing import Optional

from app.schemas.restaurant import PaginationMetadata


# Request schemas
class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    restaurant_id: int


# Response schemas
class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    is_available: bool
    restaurant_id: int

    class Config:
        from_attributes = True


class MenuItemCreatedResponse(BaseModel):
    message: str


class MenuItemListResponse(BaseModel):
    items: list[MenuItemResponse]
    pagination_metadata: PaginationMetadata


class MenuItemAvailabilityUpdatedResponse(BaseModel):
    message: str
