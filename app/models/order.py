import uuid
from sqlalchemy import ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))

    status: Mapped[str] = mapped_column(String(50), default="CREATED")
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    user = relationship("User")
    restaurant = relationship("Restaurant")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete")
