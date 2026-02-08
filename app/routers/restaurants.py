from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.dependencies import get_db
from app.core.rbac import require_roles
from app.models import Restaurant, Country
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantCreatedResponse,
    RestaurantListResponse,
    RestaurantResponse,
    PaginationMetadata,
)
from app.schemas.errors import (
    build_responses,
    UNAUTHORIZED_401,
    FORBIDDEN_403,
    BAD_REQUEST_400,
    VALIDATION_422,
    INTERNAL_SERVER_ERROR_500,
    AUTHENTICATED_FORBIDDEN_RESPONSES,
)

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.post(
    "/",
    response_model=RestaurantCreatedResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
    responses=build_responses(
        UNAUTHORIZED_401, FORBIDDEN_403, BAD_REQUEST_400,
        VALIDATION_422, INTERNAL_SERVER_ERROR_500,
    ),
    summary="Create a new restaurant",
)
async def create_restaurant(
    data: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new restaurant. Requires **ADMIN** role.

    **Possible errors:**
    - **400** – Invalid country provided.
    - **401** – Missing or invalid authentication token.
    - **403** – Insufficient permissions (ADMIN role required).
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
    country = await db.scalar(select(Country).where(Country.name == data.country.value))
    if not country:
        raise HTTPException(status_code=400, detail="Invalid country")

    restaurant = Restaurant(name=data.name, country_id=country.id)
    db.add(restaurant)
    await db.commit()
    await db.refresh(restaurant)

    return RestaurantCreatedResponse(message="Restaurant created")


@router.get(
    "/",
    response_model=RestaurantListResponse,
    responses=AUTHENTICATED_FORBIDDEN_RESPONSES,
    summary="List restaurants",
)
async def get_restaurants(
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Retrieve a paginated list of restaurants.
    Non-admin users only see restaurants in their own country.

    **Possible errors:**
    - **401** – Missing or invalid authentication token.
    - **403** – Insufficient permissions for this action.
    - **422** – Query parameters failed validation.
    - **500** – Unexpected server error.
    """
    query = (
        select(Restaurant)
        .options(selectinload(Restaurant.country))
        .offset(skip)
        .limit(limit)
    )
    count_query = select(func.count(Restaurant.id))

    if current_user.role.name != "ADMIN":
        query = query.where(Restaurant.country_id == current_user.country_id)
        count_query = count_query.where(
            Restaurant.country_id == current_user.country_id
        )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(query)
    restaurants = result.scalars().all()

    items = [
        RestaurantResponse(id=r.id, name=r.name, country=r.country.name)
        for r in restaurants
    ]
    num_items = len(items)
    start = skip + 1 if num_items > 0 else 0
    end = skip + num_items

    return RestaurantListResponse(
        items=items,
        pagination_metadata=PaginationMetadata(
            total=total,
            skip=skip,
            limit=limit,
            start=start,
            end=end,
        ),
    )
