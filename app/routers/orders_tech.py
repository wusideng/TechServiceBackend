#  订单信息


from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.core.database import engine
from app.model.t_order import T_Order


router = APIRouter(
    prefix="/ordersTech",
    tags=["ordersTech"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


# 技师查看自己的订单
@router.get("/orderList/{user_id}")
async def read_orders(user_id: str, pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(
            select(T_Order).where(T_Order.tech_user_id == user_id)
        ).all()
        total_count = len(total_count)
        statement = (
            select(T_Order)
            .where(T_Order.tech_user_id == user_id)
            .order_by(T_Order.order_id.desc())
            .offset(offset)  # 添加 offset
            .limit(pageSize)  # 添加 limit
        )
        orders = session.exec(statement).all()
        # 整合信息
        order_list = []
        for order in orders:
            order_info = {
                "order_id": order.order_id,
                "order_serial": order.order_serial,
                "create_order_time": order.create_order_time,
                "update_order_time": order.update_order_time,
                "service_time": order.service_time,
                "payment_status": order.payment_status,
                "service_address": order.service_address,
                "service_province": order.service_province,
                "service_city": order.service_city,
                "service_district": order.service_district,
                "service_street": order.service_street,
                "service_region": order.service_region,
                "service_detail_address": order.service_detail_address,
                "travel_distance": order.travel_distance,
                "travel_cost": order.travel_cost,
                "coupon_value": order.coupon_value,
                "order_cost": order.order_cost,
                "remark": order.remark,
                "client": order.client,
                "tech": order.tech,
                "order_products": order.order_products,
                "order_status": order.order_status,
            }
            order_list.append(order_info)

        return order_list
