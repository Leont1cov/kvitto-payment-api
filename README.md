# Kvitto Payment API

REST API для создания и обработки платежей онлайн-школы. Проект выполнен в рамках тестового задания на позицию Junior Python Developer.

## Технологии

- Python 3.11+
- FastAPI
- Pydantic v2
- PostgreSQL
- SQLAlchemy
- pytest
- httpx

## Возможности

- Получение списка тарифов.
- Создание платежей с использованием тарифов.
- Применение промокода `KVITTO10` со скидкой 10%.
- Поддержка способов оплаты `card`, `sbp` и `installment`.
- Расчёт графика рассрочки на 3, 6 или 12 месяцев.
- Защита от повторного создания платежа с помощью `Idempotency-Key`.
- Получение информации о платеже по ID.
- Обработка банковских webhook-уведомлений.
- Проверка допустимых переходов статусов платежа.
- Автоматическое тестирование API.

Все денежные суммы хранятся и передаются в копейках целыми числами.

## Запуск проекта

### 1. Установка зависимостей

Требуется Python 3.11 или новее и установленный PostgreSQL.

Клонируйте репозиторий и перейдите в его директорию:

```bash
git clone <ссылка-на-репозиторий>
cd <папка-проекта>
```

Создайте виртуальное окружение:

```bash
py -m venv .venv
```

Активируйте его в Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Установите зависимости:

```bash
py -m pip install -r requirements.txt
```

### 2. Настройка базы данных

Создайте базу данных PostgreSQL с именем `kvitto_payment_api`.

В корне проекта создайте файл `.env` и укажите параметры подключения:

```env
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kvitto_payment_api
```

Замените `your_password` на пароль своего пользователя PostgreSQL. Если приложение использует дополнительные переменные окружения, укажите их согласно настройкам проекта.

Не добавляйте `.env` с реальными паролями и секретами в Git.

### 3. Запуск приложения

Из корневой директории проекта выполните:

```bash
py -m uvicorn app.main:app --reload
```

После запуска API будет доступно по адресу `http://127.0.0.1:8000`.

Интерактивная документация Swagger: `http://127.0.0.1:8000/docs`.

## API

### 1. Получение тарифов

`GET /tariffs`

```bash
curl http://127.0.0.1:8000/tariffs
```

Возвращает список тарифов: `basic`, `standard` и `premium`. Стоимость передаётся в копейках.

### 2. Создание платежа

`POST /payments`

Пример создания платежа за тариф `standard` с оплатой картой:

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "tariff_id": "standard",
    "email": "user@example.com",
    "method": "card"
  }'
```

Для применения промокода добавьте поле `"promo_code": "KVITTO10"`.

Пример создания рассрочки на 3 месяца:

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "tariff_id": "standard",
    "email": "user@example.com",
    "method": "installment",
    "installment_months": 3
  }'
```

При успешном создании возвращается HTTP `201`. При повторном запросе с уже использованным ключом идемпотентности возвращается существующий платёж с HTTP `200`.

Пример использования `Idempotency-Key`:

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-123" \
  -d '{
    "tariff_id": "basic",
    "email": "user@example.com",
    "method": "card"
  }'
```

При повторном запросе передайте тот же ключ, чтобы не создать второй платёж.

### 3. Получение платежа

`GET /payments/{id}`

```bash
curl http://127.0.0.1:8000/payments/<payment_id>
```

Возвращает информацию о платеже. Если платёж не найден, возвращается HTTP `404`.

### 4. Банковский webhook

`POST /webhooks/bank`

Пример уведомления об успешной оплате:

```bash
curl -X POST http://127.0.0.1:8000/webhooks/bank \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "<payment_id>",
    "status": "succeeded"
  }'
```

Поддерживаемые переходы статусов:

- `pending` → `succeeded`
- `pending` → `failed`
- `succeeded` → `refunded`

При успешной обработке возвращается HTTP `200` с ответом `{"result": "ok"}`. Если платёж не найден, возвращается `404`. Запрещённый переход возвращает HTTP `409` с ответом `{"error": "invalid_transition"}`, при этом статус не меняется.

Ошибки валидации возвращаются с HTTP `422`.

## Запуск тестов

Выполните команду из корневой директории проекта:

```bash
py -m pytest -v
```

Тесты проверяют получение тарифов, применение промокода, расчёт графика рассрочки, идемпотентность платежей, обработку статусов и ошибки при работе с несуществующими платежами.

## Структура проекта

- `app/routers/` — API-эндпоинты.
- `app/services/` — бизнес-логика платежей.
- `app/models/` — модели базы данных.
- `app/schemas/` — схемы запросов и ответов.
- `app/database.py` — подключение к базе данных.
- `tests/` — автоматические тесты.
- `AI_LOG.md` — журнал использования ИИ при разработке.
