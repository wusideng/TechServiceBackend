#  订单信息
import json
from dateutil.relativedelta import relativedelta

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine, get_session
from app.lib.utils.coupon import group_coupons
from app.model.q_Coupon import SendCompensateCoupons
from app.model.t_coupon import T_Coupon
from app.model.q_OrderCreate import AddCouponeRequest
from logger import logger

router = APIRouter()

router = APIRouter(
    prefix="/coupon",
    tags=["coupon"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_user_auths(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Coupon)).all()
        total_count = len(total_count)
        statement = (
            select(T_Coupon).order_by(T_Coupon.coupon_id).offset(offset).limit(pageSize)
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


@router.get("/{open_id}")
async def read_user_auth(open_id: str):
    with Session(engine) as session:

        statement = select(T_Coupon).where(
            T_Coupon.open_id == open_id,
            T_Coupon.expiration_time > datetime.now(),
            or_(T_Coupon.coupon_status != "used", T_Coupon.coupon_status.is_(None)),
        )
        results = session.exec(statement)
        return results.all()


@router.post("/")
async def create_user_auth(coupon: T_Coupon):
    try:
        with Session(engine) as session:
            existing_user_auth = session.exec(
                select(T_Coupon).where(T_Coupon.coupon_id == coupon.coupon_id)
            ).first()
            if existing_user_auth:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(coupon)
                session.commit()
                session.refresh(coupon)
                return {"msg": "create sucess", "data": coupon}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/insert")
async def insert_coupons(
    coupon_request: AddCouponeRequest, session: Session = Depends(get_session)
):
    try:
        session.add_all(coupon_request.coupons)  # 添加所有优惠券
        session.commit()  # 提交事务
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_user_auth(coupon_id: int, newOrderProd: T_Coupon):
    with Session(engine) as session:
        statement = select(T_Coupon).where(T_Coupon.coupon_id == coupon_id)
        result = session.exec(statement)
        user_auth = result.one()
        user_auth.open_id = newOrderProd.open_id
        user_auth.amount = newOrderProd.amount
        session.add(user_auth)
        session.commit()
        session.refresh(user_auth)
        return user_auth


@router.post("/del/{coupon_id}")
async def delete_user_auth(coupon_id: int):
    with Session(engine) as session:
        statement = select(T_Coupon).where(T_Coupon.coupon_id == coupon_id)
        results = session.exec(statement)
        user_auth = results.first()
        if not user_auth:
            return {"msg": "there's no user_auth", "data": ""}
        session.delete(user_auth)
        session.commit()
        return {"msg": "delete sucess", "data": user_auth}


def take_new_user_coupons(openid: str, session: Session):
    with open("app/lib/new_user_coupons.json", "r", encoding="utf-8") as f:
        coupons = json.load(f)
    insert_coupons = []
    for coupon in coupons:
        # 获取数量，默认为1
        coupon_amount = int(coupon["amount"])
        expiration_time = (
            (datetime.now() + relativedelta(months=3))
            .replace(hour=23, minute=59, second=59, microsecond=0)
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        for _ in range(coupon_amount):
            insert_coupons.append(
                {
                    "open_id": openid,
                    "amount": int(coupon["coupon_value"]),  # 这里是优惠券的面值
                    "condition": int(coupon["coupon_condition"]),
                    "project": "new_user",
                    "expiration_time": expiration_time,
                    "grant_city": "默认城市",
                    "coupon_type": "新人特惠",
                    "msg": "新人特惠",
                }
            )
    coupon_objects = [T_Coupon(**coupon_data) for coupon_data in insert_coupons]
    session.add_all(coupon_objects)


@router.post("/send_compensate_coupons")
def send_compensate_coupons(
    request: SendCompensateCoupons, session: Session = Depends(get_session)
):
    expire_months = 6
    client_user_openid = request.client_user_openid
    coupons = request.coupons
    order_id = request.order_id
    insert_coupons = []
    for coupon in coupons:
        # 获取数量，默认为1
        coupon_amount = coupon.amount
        expiration_time = (
            (datetime.now() + relativedelta(months=expire_months))
            .replace(hour=23, minute=59, second=59, microsecond=0)
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        for _ in range(coupon_amount):
            msg = {"order_id": order_id}
            msg = str(msg)
            insert_coupons.append(
                {
                    "open_id": client_user_openid,
                    "amount": int(coupon.coupon_value),  # 这里是优惠券的面值
                    "condition": 0,
                    "project": "compensate",
                    "expiration_time": expiration_time,
                    "grant_city": "默认城市",
                    "coupon_type": "暖心补偿",
                    "msg": msg,
                }
            )
    coupon_objects = [T_Coupon(**coupon_data) for coupon_data in insert_coupons]
    session.add_all(coupon_objects)
    session.commit()
    compensate_coupons_statement = select(T_Coupon).where(
        T_Coupon.project == "compensate",
        T_Coupon.msg == str({"order_id": order_id}),
    )
    compensate_coupons = session.exec(compensate_coupons_statement).all()
    compensate_coupons = group_coupons(compensate_coupons)
    return {
        "order_id": order_id,
        "compensate_coupons": compensate_coupons,
    }
