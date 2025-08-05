#  订单信息
from fastapi import APIRouter, Depends, HTTPException
from httpx import Response
from sqlalchemy import delete
from sqlmodel import Session, select
from app.core.database import get_session
from app.model.t_travel_cost_base import T_Travel_Cost_Base
from logger import logger

router = APIRouter()

router = APIRouter(
    prefix="/travel_cost",
    tags=["travel_cost"],
)


@router.get("/travel_costs")
async def getTravelCosts(session=Depends(get_session)):
    try:
        return get_all_travel_costs(session)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail=str(e))


# 更新travel_costs
@router.post("/travel_costs/{id}")
async def updateCouponActivities(
    id: int,
    travel_cost_update: T_Travel_Cost_Base,
    session=Depends(get_session),
):
    city = travel_cost_update.city
    statement = select(T_Travel_Cost_Base).where(
        T_Travel_Cost_Base.city == city, T_Travel_Cost_Base.id != id
    )
    result = session.exec(statement).first()
    if result:
        raise HTTPException(status_code=409, detail=f"{city}打车费设定已经存在")
    statement = select(T_Travel_Cost_Base).where(T_Travel_Cost_Base.id == id)
    travel_cost = session.exec(statement).first()

    for key, value in travel_cost_update.model_dump(exclude={"activity_id"}).items():
        if key != "create_time":
            setattr(travel_cost, key, value)
    session.commit()
    return Response(status_code=200)


@router.delete("/travel_costs/{id}")
async def deleteTravelCost(id: int, session=Depends(get_session)):
    try:
        # 获取要删除的activity
        delete_stmt = delete(T_Travel_Cost_Base).where(
            T_Travel_Cost_Base.id == id,
        )
        session.exec(delete_stmt)
        session.commit()
        return get_all_travel_costs(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail="other error")


# 新增coupon活动
@router.put("/travel_costs")
async def create_travel_cost(
    travel_cost: T_Travel_Cost_Base, session=Depends(get_session)
):
    city = travel_cost.city
    statement = select(T_Travel_Cost_Base).where(T_Travel_Cost_Base.city == city)
    result = session.exec(statement).first()
    if result:
        raise HTTPException(status_code=409, detail=f"{city}打车费设定已经存在")
    session.add(travel_cost)
    session.commit()
    return Response(status_code=200)


def get_all_travel_costs(session: Session):
    statement = select(T_Travel_Cost_Base).order_by(
        T_Travel_Cost_Base.create_time.desc()
    )
    travel_costs = session.exec(statement).all()
    return travel_costs


@router.get("/city/{city}")
def get_travel_cost_by_city(city: str, session: Session = Depends(get_session)):
    statement = select(T_Travel_Cost_Base).where(T_Travel_Cost_Base.city == city)
    travel_cost = session.exec(statement).first()
    travel_cost = travel_cost.model_dump()
    if not travel_cost:
        travel_cost = get_default_travel_cost(city)
    return travel_cost


def get_default_travel_cost(city):
    default_travel_cost = {
        "city": city,
        "base_price": 14,
        "base_distance_km": 3,
        "price_per_km_daytime": 2.5,
        "price_per_km_nighttime": 3,
        "night_hour": 22,
    }
    return default_travel_cost
