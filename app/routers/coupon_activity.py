#  订单信息
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlmodel import Session, select
from starlette.responses import Response

from app.core.database import get_session
from app.model.q_Coupon import TakeCouponsFromActivity
from app.model.t_coupon import T_Coupon
from app.model.t_coupon_activity import T_Coupon_Activity
from logger import logger

router = APIRouter()

router = APIRouter(
    prefix="/coupon_activity",
    tags=["coupon_activity"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/coupon_activities")
async def getCouponActivities(session=Depends(get_session)):
    try:
        return get_all_coupon_activities(session)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail="other error.")


@router.get("/get_valid_coupon_activity")
async def getCouponActivity(
    openid: Optional[str] = None, session: Session = Depends(get_session)
):
    try:
        now = datetime.now()
        latest_active_activity_statement = (
            select(T_Coupon_Activity)
            .where(
                T_Coupon_Activity.activity_status == "active",
                T_Coupon_Activity.start_time <= now,
                T_Coupon_Activity.end_time >= now,
            )
            .order_by(T_Coupon_Activity.create_time.desc())
        )

        coupon_activity = session.exec(latest_active_activity_statement).first()
        if not coupon_activity:
            return None
        if openid and openid != "":
            user_coupon = session.exec(
                select(T_Coupon.coupon_id)
                .where(
                    T_Coupon.open_id == openid,
                    T_Coupon.activity_id == coupon_activity.activity_id,
                )
                .limit(1)
            ).first()
            if user_coupon:
                return None
        return coupon_activity
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail="other error.")


# 更新coupon活动
@router.post("/coupon_activities/{activity_id}")
async def updateCouponActivities(
    activity_id: int,
    coupon_activity_update: T_Coupon_Activity,
    session=Depends(get_session),
):
    try:
        statement = select(T_Coupon_Activity).where(
            T_Coupon_Activity.activity_id == activity_id
        )
        coupon_activity = session.exec(statement).first()

        for key, value in coupon_activity_update.model_dump(
            exclude={"activity_id"}
        ).items():
            if key != "create_time":
                setattr(coupon_activity, key, value)
        session.commit()
        return get_all_coupon_activities(session)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail="other error.")


@router.delete("/coupon_activities/{activity_id}")
async def deleteCouponActivities(activity_id: int, session=Depends(get_session)):
    try:
        # 获取要删除的activity
        delete_stmt = delete(T_Coupon_Activity).where(
            T_Coupon_Activity.activity_id == activity_id,
        )
        session.exec(delete_stmt)
        session.commit()
        return get_all_coupon_activities(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 新增coupon活动
@router.put("/coupon_activities")
async def create_coupon_activity(
    coupon_activity: T_Coupon_Activity, session=Depends(get_session)
):
    try:
        session.add(coupon_activity)
        session.commit()

        return get_all_coupon_activities(session)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail="other error.")


# 用户领取coupon活动优惠券
@router.post("/take_coupons")
async def client_user_take_coupons_from_activity(
    request: TakeCouponsFromActivity, session: Session = Depends(get_session)
):
    openid = request.openid
    activity_id = request.activity_id
    city = request.city
    existing_coupon_statement = (
        select(T_Coupon)
        .where(T_Coupon.open_id == openid, T_Coupon.activity_id == activity_id)
        .limit(1)
    )
    user_coupon = session.exec(existing_coupon_statement).first()
    if user_coupon:
        raise HTTPException(status_code=208, detail="already have coupons.")
    coupon_activity_statement = select(T_Coupon_Activity).where(
        T_Coupon_Activity.activity_id == activity_id
    )
    coupon_activity = session.exec(coupon_activity_statement).first()
    now = datetime.now()
    if not (coupon_activity.start_time <= now <= coupon_activity.end_time):
        raise ValueError("活动不在有效时间范围内")
    coupons = json.loads(coupon_activity.coupons)
    insert_coupons = []
    for coupon in coupons:
        # 获取数量，默认为1
        coupon_amount = int(coupon["amount"])
        for _ in range(coupon_amount):
            insert_coupons.append(
                {
                    "open_id": openid,
                    "amount": int(coupon["coupon_value"]),  # 这里是优惠券的面值
                    "condition": int(coupon["coupon_condition"]),
                    "project": "activity",
                    "expiration_time": coupon_activity.end_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "activity_id": int(activity_id),
                    "grant_city": city,
                    "coupon_type": coupon_activity.activity_name,
                    "msg": coupon_activity.activity_name,
                }
            )
    coupon_objects = [T_Coupon(**coupon_data) for coupon_data in insert_coupons]
    session.add_all(coupon_objects)
    session.commit()
    return Response(status_code=200)


def get_all_coupon_activities(session: Session):
    statement = select(T_Coupon_Activity).order_by(T_Coupon_Activity.create_time.desc())
    coupon_activities = session.exec(statement).all()
    response = []
    for coupon_activity in coupon_activities:
        coupons = coupon_activity.get_coupons()
        coupon_activity = coupon_activity.model_dump()
        coupon_activity["coupons"] = coupons
        response.append(coupon_activity)
    return response
