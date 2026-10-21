from fastapi import APIRouter, HTTPException, Response
from fastapi.params import Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tariff, Payment
from app.schemas.payment import PaymentResponse, PaymentCreate, BankWebhook
from app.services.payment_service import create_schedule

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
        payment_data: PaymentCreate,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'), #уникальный ключ, чтобы случайно не создавать дважды один и тот же платёж (Header - берем значение из заголовка запроса)
        db: Session = Depends(get_db)):

    #Проверяем, не создавали ли уже платёж с таким же ключом
    if idempotency_key is not None:
        #если ключ передан - ищем в БД платёж с таким же ключом
        existing_payment = db.query(Payment).filter(
            Payment.idempotency_key == idempotency_key
        ).first()
        if existing_payment is not None:
            #если платёж найден - возвращаем 200, не создавая новый платёж
            response.status_code = 200 #изменяем HTTP статус ответа
            return existing_payment


    #Проверка тарифа
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
        idempotency_key=idempotency_key,
        email=payment_data.email,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

#Проверяем разрешен ли переход платежа из одного статуса в другой, если разрешен -> обновляем статус в БД
#функция уведомления от банка
@router.post("/webhooks/bank")
def bank_webhook(webhook: BankWebhook, db: Session = Depends(get_db)):
    payment = db.get(Payment, webhook.payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    #словарь разрешенных переходов
    allowed_transitions = {
        "pending": ["succeeded", "failed"],
        "succeeded": ["refunded"],
        "failed": [],
        "refunded": [],
    }
    if webhook.status not in allowed_transitions[payment.status]:
        return JSONResponse(status_code=409, content={"error": "invalid_transition"})
    payment.status = webhook.status
    db.commit()

    return {"result": "ok"}