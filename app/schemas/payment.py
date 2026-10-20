from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    tariff_id: str
    email: str
    method: Literal["card", "sbp", "installment"]
    installment_months: int | None = None
    promo_code: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    tariff_id: str
    amount: int
    discount: int
    method: str
    installment_months: int | None
    schedule: list[int] | None
    email: str
    created_at: datetime