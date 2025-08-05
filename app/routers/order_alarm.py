#  订单信息

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.model.t_order_alarm import T_Order_Alarm

router = APIRouter()

router = APIRouter(
    prefix="/orderAlarm",
    tags=["orderAlarm"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_orders(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Order_Alarm)).all()
        total_count = len(total_count)
        statement = (
            select(T_Order_Alarm)
            .order_by(T_Order_Alarm.alarm_id)
            .offset(offset)
            .limit(pageSize)
        )
        orders = session.exec(statement).all()
        return {
            "total_count": total_count,
            "data": orders,
            "page": pageNum,
            "page_size": pageSize,
            "total_pages": (total_count // pageSize)
            + (1 if total_count % pageSize > 0 else 0),
        }


@router.get("/{alarm_id}")
async def read_order(alarm_id: str):
    with Session(engine) as session:
        statement = select(T_Order_Alarm).where(T_Order_Alarm.alarm_id == alarm_id)
        results = session.exec(statement)
        return results.first()


@router.post("/")
async def create_order(order_comment: T_Order_Alarm):
    try:
        with Session(engine) as session:
            existing_order = session.exec(
                select(T_Order_Alarm).where(
                    T_Order_Alarm.alarm_id == order_comment.alarm_id
                )
            ).first()
            if existing_order:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(order_comment)
                session.commit()
                session.refresh(order_comment)
                return {"msg": "create sucess", "data": order_comment}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_order(alarm_id: int, newOrderProd: T_Order_Alarm):
    with Session(engine) as session:
        statement = select(T_Order_Alarm).where(T_Order_Alarm.alarm_id == alarm_id)
        result = session.exec(statement)
        order = result.one()
        order.alarm_status = newOrderProd.alarm_status
        order.order_id = newOrderProd.order_id
        order.time_stamp = newOrderProd.time_stamp
        order.information = newOrderProd.information
        order.ramark = newOrderProd.ramark
        session.add(order)
        session.commit()
        session.refresh(order)
        return order


@router.post("/del/{alarm_id}")
async def delete_order(alarm_id: int):
    with Session(engine) as session:
        statement = select(T_Order_Alarm).where(T_Order_Alarm.alarm_id == alarm_id)
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}
