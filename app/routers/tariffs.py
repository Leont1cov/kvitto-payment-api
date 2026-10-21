from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tariff
from app.schemas.tariff import TariffResponse

router = APIRouter(prefix="/tariffs", tags=["Tariffs"])

@router.get("/", response_model=list[TariffResponse])
def get_tariffs(db: Session = Depends(get_db)):
    tariffs = db.query(Tariff).all()
    return tariffs