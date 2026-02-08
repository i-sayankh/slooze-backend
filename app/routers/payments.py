from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.core.dependencies import get_db
from app.core.rbac import require_roles
from app.models import PaymentMethod
from app.schemas.payment import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodResponse,
    PaymentMethodCreatedResponse,
    PaymentMethodListResponse,
    PaymentMethodUpdatedResponse,
)
from app.schemas.restaurant import PaginationMetadata
from app.schemas.errors import (
    AUTHENTICATED_FORBIDDEN_RESPONSES,
    AUTHENTICATED_FORBIDDEN_NOT_FOUND_RESPONSES,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/",
    response_model=PaymentMethodCreatedResponse,
    responses=AUTHENTICATED_FORBIDDEN_RESPONSES,
    summary="Add a payment method",
)
async def add_payment_method(
    data: PaymentMethodCreate,
    current_user=Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new payment method. Requires **ADMIN** role.
    If ``is_default`` is true, all other payment methods for the user are un-defaulted.

    **Possible errors:**
    - **401** – Missing or invalid authentication token.
    - **403** – Insufficient permissions (ADMIN role required).
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
    if data.is_default:
        await db.execute(
            update(PaymentMethod)
            .where(PaymentMethod.user_id == current_user.id)
            .values(is_default=False)
        )

    payment = PaymentMethod(
        user_id=current_user.id,
        type=data.type,
        provider=data.provider,
        last_four=data.last_four,
        is_default=data.is_default,
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentMethodCreatedResponse(message="Payment method added", id=payment.id)


@router.get(
    "/",
    response_model=PaymentMethodListResponse,
    responses=AUTHENTICATED_FORBIDDEN_RESPONSES,
    summary="List payment methods",
)
async def get_payments(
    current_user=Depends(require_roles("ADMIN", "MANAGER", "MEMBER")),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Retrieve a paginated list of all payment methods.

    **Possible errors:**
    - **401** – Missing or invalid authentication token.
    - **403** – Insufficient permissions for this action.
    - **422** – Query parameters failed validation.
    - **500** – Unexpected server error.
    """
    count_result = await db.execute(
        select(func.count(PaymentMethod.id))
    )
    total = count_result.scalar()

    result = await db.execute(
        select(PaymentMethod).offset(skip).limit(limit)
    )
    payment_methods = result.scalars().all()

    items = [PaymentMethodResponse.model_validate(p) for p in payment_methods]
    num_items = len(items)
    start = skip + 1 if num_items > 0 else 0
    end = skip + num_items

    return PaymentMethodListResponse(
        items=items,
        pagination_metadata=PaginationMetadata(
            total=total,
            skip=skip,
            limit=limit,
            start=start,
            end=end,
        ),
    )


@router.put(
    "/{payment_id}",
    response_model=PaymentMethodUpdatedResponse,
    responses=AUTHENTICATED_FORBIDDEN_NOT_FOUND_RESPONSES,
    summary="Update a payment method",
)
async def update_payment_method(
    payment_id: int,
    data: PaymentMethodUpdate,
    current_user=Depends(require_roles("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing payment method. Requires **ADMIN** role.

    **Possible errors:**
    - **401** – Missing or invalid authentication token.
    - **403** – Insufficient permissions (ADMIN role required).
    - **404** – The specified payment method does not exist.
    - **422** – Request body failed validation.
    - **500** – Unexpected server error.
    """
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment method not found")

    if data.provider is not None:
        payment.provider = data.provider

    if data.is_default is not None:
        payment.is_default = data.is_default

    await db.commit()

    return PaymentMethodUpdatedResponse(message="Payment method updated")
