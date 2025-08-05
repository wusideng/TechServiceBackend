from fastapi import APIRouter, Depends
from sqlalchemy import asc
from sqlmodel import Session, select
from app.core.database import get_session
from app.model.t_open_cities import T_Open_Cities

router = APIRouter(
    prefix="/city",
    tags=["city"],
)


@router.get("/open_cities")
async def get_open_cities(
    session: Session = Depends(get_session),
):
    cities = session.exec(
        select(T_Open_Cities.city).order_by(asc(T_Open_Cities.city_order))
    ).all()
    return cities
