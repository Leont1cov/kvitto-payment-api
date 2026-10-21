from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tariff, Payment
from app.schemas.payment import PaymentResponse, PaymentCreate
from app.services.payment_service import create_schedule

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    tariff = db.get(Tariff, payment_data.tariff_id)

    if tariff is None:
        raise HTTPException(status_code=404, detail="Tariff not found")

    #Расчёт скидки
    discount = 0 #скидка

    if payment_data.promo_code is not None:
        if payment_data.promo_code.upper() != "KVITTO10":
            raise HTTPException(status_code=404, detail="Promo code is not supported")

        discount = tariff.price // 10

    amount = tariff.price - discount #итоговая стоимость

    #Проверка рассрочки и рассчёт графика платежей
    schedule = None #график платежей

    if payment_data.method == "installment":
        if payment_data.installment_months not in [3, 6, 12]: #допустимы только 3,6,12 месяцев
            raise HTTPException(status_code=422, detail="Invalid installment months")
        schedule = create_schedule(amount, payment_data.installment_months) #распределяем итогувую сумму по месяцам

    import uuid

    payment = Payment(
        id=str(uuid.uuid4()), # генерирует уникальный ID платежа
        status="pending",
        tariff_id=tariff.id,
        amount=amount,
        discount=discount,
        method=payment_data.method,
        installment_months=payment_data.installment_months,
        schedule=schedule,
        email=payment_data.email,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment