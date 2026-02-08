from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.core.dependencies import get_db
from app.core.rbac import require_roles
from app.models import Order, OrderItem, Restaurant, MenuItem, PaymentMethod
from app.schemas.order import (
    GetOrdersQuery,
    OrderCreate,
    OrderCreateResponse,
    OrderItemDetail,
    OrderListResponse,
    OrderResponse,
    AddItemRequest,
    AddItemResponse,
    CheckoutRequest,
    CheckoutResponse,
    CancelOrderResponse,
)
from app.schemas.restaurant import PaginationMetadata
from app.schemas.errors import (
    AUTHENTICATED_FORBIDDEN_RESPONSES,
    AUTHENTICATED_FORBIDDEN_NOT_FOUND_RESPONSES,
    AUTHENTICATED_ALL_RESPONSES,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_orders_query(
    restaurant_id: Optional[int] = Query(None, description="Filter orders by restaurant ID"),
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max number of orders to return"),
) -> GetOrdersQuery:
    return GetOrdersQuery(restaurant_id=restaurant_id, skip=skip, limit=limit)


@router.get(
    "/",
    response_model=OrderListResponse,
    responses=AUTHENTICATED_FORBIDDEN_RESPONSES,
    summary="List all orders",
)
async def list_orders(
    query: GetOrdersQuery = Depends(get_orders_query),
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
):
    """
    List all orders with optional filtering by restaurant.
    Non-admin users only see orders from restaurants in their country.

    **Possible errors:**
    - **401** – Missing or invalid authentication token.
    - **403** – Insufficient permissions for this action.
    - **422** – Query parameters failed validation.
    - **500** – Unexpected server error.
    """
    base = (
        select(Order)
        .options(
            selectinload(Order.restaurant),
            selectinload(Order.items).selectinload(OrderItem.menu_item),
        )
    )
    count_stmt = select(func.count(Order.id))

    # Country-based restriction for non-admin users
    if current_user.role.name != "ADMIN":
        base = base.join(Restaurant, Order.restaurant_id == Restaurant.id).where(
            Restaurant.country_id == current_user.country_id
        )
        count_stmt = count_stmt.join(Restaurant, Order.restaurant_id == Restaurant.id).where(
            Restaurant.country_id == current_user.country_id
        )

    if query.restaurant_id is not None:
        base = base.where(Order.restaurant_id == query.restaurant_id)
        count_stmt = count_stmt.where(Order.restaurant_id == query.restaurant_id)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(Order.id).offset(query.skip).limit(query.limit)
    )
    orders = result.scalars().all()

    items = [
        OrderResponse(
            id=o.id,
            user_id=o.user_id,
            restaurant_id=o.restaurant_id,
            restaurant_name=o.restaurant.name,
            status=o.status,
            total_amount=float(o.total_amount),
            items=[
                OrderItemDetail(
                    menu_item_name=item.menu_item.name,
                    quantity=item.quantity,
                    price=float(item.price),
                )
                for item in o.items
            ],
        )
        for o in orders
    ]

    num_items = len(items)
    start = query.skip + 1 if num_items > 0 else 0
    end = query.skip + num_items

    return OrderListResponse(
        items=items,
        pagination_metadata=PaginationMetadata(
            total=total,
            skip=query.skip,
            limit=query.limit,
            start=start,
            end=end,
        ),
    )


@router.post(
    "/",
    response_model=OrderCreateResponse,
    responses=AUTHENTICATED_FORBIDDEN_NOT_FOUND_RESPONSES,
    summary="Create a new order",
)
async def create_order(
    data: OrderCreate,
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new order for a restaurant.
    Non-admin users can only create orders at restaurants in their country.

    **Possible errors:**
    - **401** – Missing or invalid authentication token.
    - **403** – You do not have access to this restaurant (country restriction).
    - **404** – The specified restaurant does not exist.
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
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


@router.post(
    "/{order_id}/items",
    response_model=AddItemResponse,
    responses=AUTHENTICATED_ALL_RESPONSES,
    summary="Add an item to an order",
)
async def add_item(
    order_id: UUID,
    data: AddItemRequest,
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a menu item to an existing order.
    Only the order owner (or ADMIN) may add items. The order must still be in CREATED status.

    **Possible errors:**
    - **400** – Order has already been finalized.
    - **401** – Missing or invalid authentication token.
    - **403** – You are not the owner of this order.
    - **404** – Order or menu item not found / unavailable.
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
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


@router.post(
    "/{order_id}/checkout",
    response_model=CheckoutResponse,
    responses=AUTHENTICATED_ALL_RESPONSES,
    summary="Checkout an order",
)
async def checkout_order(
    order_id: UUID,
    data: CheckoutRequest,
    current_user=Depends(require_roles("ADMIN", "MANAGER")),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize an order and mark it as PLACED.
    Requires **ADMIN** or **MANAGER** role. Non-admin users can only checkout their own orders.

    **Possible errors:**
    - **400** – Order has already been processed.
    - **401** – Missing or invalid authentication token.
    - **403** – You are not the owner of this order.
    - **404** – Order or payment method not found.
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Ownership check: non-admin users can only checkout their own orders
    if current_user.role.name != "ADMIN":
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied: not your order")

    if order.status != "CREATED":
        raise HTTPException(status_code=400, detail="Already processed")

    # Validate payment method exists
    result = await db.execute(
        select(PaymentMethod)
        .where(PaymentMethod.id == data.payment_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment method not found")

    order.status = "PLACED"

    await db.commit()

    return CheckoutResponse(
        order_id=order.id,
        status=order.status,
        total_amount=float(order.total_amount),
    )


@router.patch(
    "/{order_id}/cancel",
    response_model=CancelOrderResponse,
    responses=AUTHENTICATED_ALL_RESPONSES,
    summary="Cancel an order",
)
async def cancel_order(
    order_id: UUID,
    current_user=Depends(require_roles("ADMIN", "MANAGER")),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a placed order. Requires **ADMIN** or **MANAGER** role.
    Only orders in PLACED status can be cancelled.

    **Possible errors:**
    - **400** – Only placed orders can be cancelled.
    - **401** – Missing or invalid authentication token.
    - **403** – Insufficient permissions for this action.
    - **404** – The specified order does not exist.
    - **422** – Path parameter failed validation.
    - **500** – Unexpected server error.
    """
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
