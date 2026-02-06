from pydantic import BaseModel
from uuid import UUID


# --- Request schemas ---


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
