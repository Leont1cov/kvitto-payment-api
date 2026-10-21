import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Tariff, Payment

load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

DATABASE_URL = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        tariffs = [
            Tariff(id="basic", title="Basic", price=990000),
            Tariff(id="standard", title="Standard", price=1990000),
            Tariff(id="premium", title="Premium", price=2990000),
        ]

        for tariff in tariffs:
            if db.get(Tariff, tariff.id) is None:
                db.add(tariff)

        db.commit()