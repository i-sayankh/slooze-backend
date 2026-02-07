from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.schemas.restaurant import PaginationMetadata


# --- Request schemas ---


class GetOrdersQuery(BaseModel):
    """Optional query params for listing orders."""

    restaurant_id: Optional[int] = None
    skip: int = 0
    limit: int = 20


class OrderCreate(BaseModel):
    restaurant_id: int


class AddItemRequest(BaseModel):
    menu_item_id: int
    quantity: int


class CheckoutRequest(BaseModel):
    payment_id: int


# --- Response schemas ---


class OrderCreateResponse(BaseModel):
    order_id: UUID
    status: str


class AddItemResponse(BaseModel):
    message: str


class CheckoutResponse(BaseModel):
    order_id: UUID
    status: str
    total_amount: float


class CancelOrderResponse(BaseModel):
    message: str


class OrderItemDetail(BaseModel):
    """Single item within an order."""

    menu_item_name: str
    quantity: int
    price: float


class OrderResponse(BaseModel):
    """Single order in list response."""

    id: UUID
    user_id: UUID
    restaurant_id: int
    restaurant_name: str
    status: str
    total_amount: float
    items: list[OrderItemDetail]


class OrderListResponse(BaseModel):
    """Response for GET /orders."""

    items: list[OrderResponse]
    pagination_metadata: PaginationMetadata
