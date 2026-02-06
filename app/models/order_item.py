from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))

    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))

    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Numeric(10, 2))

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")
