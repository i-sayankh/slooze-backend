from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.dependencies import get_db
from app.core.rbac import require_roles
from app.models import MenuItem, Restaurant
from app.schemas.menu_item import (
    MenuItemCreate,
    MenuItemCreatedResponse,
    MenuItemListResponse,
    MenuItemResponse,
    MenuItemAvailabilityUpdatedResponse,
)
from app.schemas.restaurant import PaginationMetadata

router = APIRouter(prefix="/menu-items", tags=["Menu Items"])


@router.post(
    "/",
    response_model=MenuItemCreatedResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
async def create_menu_item(
    data: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
):
    # Validate restaurant exists
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == data.restaurant_id)
    )
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menu_item = MenuItem(
        name=data.name,
        description=data.description,
        price=data.price,
        restaurant_id=data.restaurant_id,
    )

    db.add(menu_item)
    await db.commit()
    await db.refresh(menu_item)

    return MenuItemCreatedResponse(message="Menu item created successfully")


@router.get("/{restaurant_id}", response_model=MenuItemListResponse)
async def get_menu_items(
    restaurant_id: int,
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    # Fetch restaurant first
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Country restriction
    if current_user.role.name != "ADMIN":
        if restaurant.country_id != current_user.country_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Count total items
    count_result = await db.execute(
        select(func.count(MenuItem.id)).where(MenuItem.restaurant_id == restaurant_id)
    )
    total = count_result.scalar()

    # Fetch paginated items
    query = (
        select(MenuItem)
        .where(MenuItem.restaurant_id == restaurant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    menu_items = result.scalars().all()

    items = [MenuItemResponse.model_validate(m) for m in menu_items]
    num_items = len(items)
    start = skip + 1 if num_items > 0 else 0
    end = skip + num_items

    return MenuItemListResponse(
        items=items,
        pagination_metadata=PaginationMetadata(
            total=total,
            skip=skip,
            limit=limit,
            start=start,
            end=end,
        ),
    )


@router.patch(
    "/{menu_item_id}/availability",
    response_model=MenuItemAvailabilityUpdatedResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
async def toggle_availability(
    menu_item_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == menu_item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    item.is_available = not item.is_available
    await db.commit()

    return MenuItemAvailabilityUpdatedResponse(message="Availability updated")
