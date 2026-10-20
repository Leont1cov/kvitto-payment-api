from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from .base import Base

class Payment(Base):
    __tablename__ = 'payments'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String)
    tariff_id: Mapped[str] = mapped_column(String, ForeignKey("tariffs.id"))

    amount: Mapped[int] = mapped_column(Integer)
    discount: Mapped[int] = mapped_column(Integer)

    method: Mapped[str] = mapped_column(String)
    installment_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    email: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc)) #без lambda платежи будут получать одно и тоже время
    schedule: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)