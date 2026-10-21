from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db

from app.routers import tariffs, payments


@asynccontextmanager #позволяет выполнить код до запуска приложения и после его завершения
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(tariffs.router)
app.include_router(payments.router)