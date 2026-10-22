import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_tariffs():
    response = client.get("/tariffs/")

    assert response.status_code == 200

    # Проверяем, что в ответе есть 3 тарифа
    assert len(response.json()) == 3

#проверка промокода с верхним регистром
def test_create_payment_with_promo():
    response = client.post("/payments/", json={
        "tariff_id": "standard",
        "email": "test@example.com",
        "method": "card",
        "promo_code": "KVITTO10"
    })

    assert response.status_code == 201

    payment = response.json()

    # Цена тарифа standard — 1 990 000 копеек.
    # Скидка 10%: 1 990 000 // 10 = 199 000 копеек.
    assert payment["amount"] ==  1_791_000 # 1 990 000 - 199 000
    assert payment["discount"] == 199_000 # 10% от стоимости тарифа

#проверка промокода с нижним регистром
def test_create_payment_with_lowercase_promo():
    response = client.post("/payments/", json={
        "tariff_id": "standard",
        "email": "test@example.com",
        "method": "card",
        "promo_code": "kvitto10"
    })

    assert response.status_code == 201

    payment = response.json()

    # Цена тарифа standard — 1 990 000 копеек.
    # Скидка 10%: 1 990 000 // 10 = 199 000 копеек.
    assert payment["amount"] ==  1_791_000 # 1 990 000 - 199 000
    assert payment["discount"] == 199_000 # 10% от стоимости тарифа

#проверка ошибочного промокода
def test_create_payment_with_wrong_promo():
    response = client.post("/payments/", json={
        "tariff_id": "standard",
        "email": "test@example.com",
        "method": "card",
        "promo_code": "INVALID"
    })

    assert response.status_code == 422

#Проверка графика рассрочки на 3,6,12 месяцев - все месячные платежи в сумме дают правильную стоимость
@pytest.mark.parametrize("months", [3, 6, 12]) #запускает тест 3 раза подставляя разные значения
def test_installment_schedule(months):
    response = client.post("/payments/", json={
        "tariff_id": "standard",
        "email": "test@example.com",
        "method": "installment",
        "installment_months": months
    })

    assert response.status_code == 201

    payment = response.json()
    schedule = payment["schedule"]

    assert len(schedule) == months
    assert sum(schedule) == payment["amount"]

    # Для 3 месяцев дополнительно проверяем распределение остатка
    if months == 3:
        assert schedule == [663334, 663333, 663333]


# Проверяем, что нельзя оформить рассрочку на 5 месяцев
def test_installment_invalid_months():
    response = client.post("/payments/", json={
        "tariff_id": "standard",
        "email": "test@example.com",
        "method": "installment",
        "installment_months": 5
    })

    assert response.status_code == 422


from uuid import uuid4 #для получения уникального ключа
#Проверка идемпотентности
def test_payment_idempotency():
    key = str(uuid4()) #уникальынй ключ для запроса
    headers = {"Idempotency-key": key}

    payment_data = {
        "tariff_id": "standard",
        "email": "test@example.com",
        "method": "card"
    }

    #первый запрос - создаём платёж
    response1 = client.post(
        "/payments/",
        json=payment_data,
        headers=headers
    )

    #повторный запрос
    response2 = client.post(
        "/payments/",
        json=payment_data,
        headers=headers
    )

    assert response1.status_code == 201 #создан новой платёж в БД
    assert response2.status_code == 200 #обнаружен существующий платёж

    payment1 = response1.json()
    payment2 = response2.json()

    assert payment1["id"] == payment2["id"]

#Проверка смены статуса платежа
def test_forbidden_status_transition():
    # Создаём новый платёж
    response = client.post("/payments/", json={
        "tariff_id": "standard",
        "email": "test@example.com",
        "method": "card"
    })

    payment_id = response.json()["id"]

    # Пытаемся вернуть деньги за незавершённый платёж
    webhook_response = client.post("/webhooks/bank", json={
        "payment_id": payment_id,
        "status": "refunded"
    })

    print("Payment ID:", payment_id)
    print("Webhook response:", webhook_response.json())

    # Проверяем, что API запретила переход
    assert webhook_response.status_code == 409
    assert webhook_response.json() == {"error": "invalid_transition"}

    # Проверяем, что статус платежа не изменился
    payment_response = client.get(f"/payments/{payment_id}")

    assert payment_response.status_code == 200
    assert payment_response.json()["status"] == "pending"

#Проверка - платёж не найден
def test_payment_not_found():
    # Запрашиваем платёж, которого нет в базе
    response = client.get("/payments/nonexistent-payment-id")

    # Проверяем, что API вернула 404
    assert response.status_code == 404

# Проверяем webhook для несуществующего платежа
def test_webhook_payment_not_found():
    response = client.post("/webhooks/bank", json={
        "payment_id": "nonexistent-payment-id",
        "status": "succeeded"
    })

    assert response.status_code == 404
