from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.dependencies import get_db
from app.core.rbac import require_roles
from app.models import Order, OrderItem, Restaurant, MenuItem
from app.schemas.order import (
    OrderCreate,
    OrderCreateResponse,
    AddItemRequest,
    AddItemResponse,
    CheckoutResponse,
    CancelOrderResponse,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderCreateResponse)
async def create_order(
    data: OrderCreate,
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == data.restaurant_id)
    )
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Country restriction
    if current_user.role.name != "ADMIN":
        if restaurant.country_id != current_user.country_id:
            raise HTTPException(status_code=403, detail="Access denied")

    order = Order(user_id=current_user.id, restaurant_id=data.restaurant_id)

    db.add(order)
    await db.commit()
    await db.refresh(order)

    return OrderCreateResponse(order_id=order.id, status=order.status)


@router.post("/{order_id}/items", response_model=AddItemResponse)
async def add_item(
    order_id: UUID,
    data: AddItemRequest,
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Ownership check
    if current_user.role.name != "ADMIN":
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not your order")

    if order.status != "CREATED":
        raise HTTPException(status_code=400, detail="Order already finalized")

    # Fetch menu item
    result = await db.execute(select(MenuItem).where(MenuItem.id == data.menu_item_id))
    menu_item = result.scalar_one_or_none()

    if not menu_item or not menu_item.is_available:
        raise HTTPException(status_code=404, detail="Menu item unavailable")

    order_item = OrderItem(
        order_id=order.id,
        menu_item_id=menu_item.id,
        quantity=data.quantity,
        price=menu_item.price,
    )

    order.total_amount += menu_item.price * data.quantity

    db.add(order_item)
    await db.commit()

    return AddItemResponse(message="Item added successfully")


@router.post("/{order_id}/checkout", response_model=CheckoutResponse)
async def checkout_order(
    order_id: UUID,
    current_user=Depends(require_roles("ADMIN", "MANAGER")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "CREATED":
        raise HTTPException(status_code=400, detail="Already processed")

    order.status = "PLACED"

    await db.commit()

    return CheckoutResponse(
        order_id=order.id,
        status=order.status,
        total_amount=float(order.total_amount),
    )


@router.patch("/{order_id}/cancel", response_model=CancelOrderResponse)
async def cancel_order(
    order_id: UUID,
    current_user=Depends(require_roles("ADMIN", "MANAGER")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "PLACED":
        raise HTTPException(
            status_code=400, detail="Only placed orders can be cancelled"
        )

    order.status = "CANCELLED"

    await db.commit()

    return CancelOrderResponse(message="Order cancelled")
