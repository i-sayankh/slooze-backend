from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from sqlalchemy.dialects.postgresql import UUID


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    type: Mapped[str] = mapped_column(String(50))  # CARD, UPI
    provider: Mapped[str] = mapped_column(String(100))
    last_four: Mapped[str] = mapped_column(String(4))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User")
