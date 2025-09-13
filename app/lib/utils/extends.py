# 加钟率
from decimal import Decimal
from sqlmodel import Session, select

from app.model.t_bill import T_Bill
from app.model.t_order import T_Order
from app.model.t_tech_user import T_Tech_User
from logger import logger


def calculate_extends_for_tech(openid, session: Session):
    total_order_count = 0   # 订单量
    extend_rate_ratio = 0   # 加钟率
    actual_total_order_count = 0    #替单量
    actual_extend_rate_ratio = 0    # 替单加钟率

    statement = select(T_Bill).where(T_Bill.openid == openid)
    results = session.scalars(statement).all()  # 获取所有结果的第一列
    bill_mapping_order_list = [bill.order_id for bill in results] 
    # -----------技师本人接单-----------
    # 接单首单
    orders = session.scalars(
        select(T_Order)
        .where(T_Order.order_id.in_(bill_mapping_order_list) &
                (T_Order.actual_tech_openid.is_(None)))
    ).all()
    order_list = [order.order_id for order in orders] 
    # 加钟列表
    extend_orders = session.scalars(
        select(T_Order)
        .where(T_Order.parent_order_id.in_(order_list))
    ).all()
    # 首单总金额
    order_sum = sum( order.actual_fee_received/100 - 2* order.travel_cost for order in orders)
    if order_sum != 0:
        # 加钟总金额
        extend_orders_sum = sum(
                (order.actual_fee_received / 100 if order.actual_fee_received is not None else 0) - 
                2 * order.travel_cost 
                for order in extend_orders
            )
        extend_rate_ratio = extend_orders_sum / order_sum
        extend_rate_ratio = round(extend_rate_ratio, 4)
        print("extend_orders_sum:", extend_orders_sum)
    # -----------技师替单-----------
    # 接单首单
    orders_actual = session.scalars(
        select(T_Order)
        .where(T_Order.order_id.in_(bill_mapping_order_list) &
                (T_Order.actual_tech_openid.isnot(None)))
    ).all()
    actual_total_order_count = len(orders_actual)
    order_actual_list = [order.order_id for order in orders_actual] 
    extend_orders_actual = session.scalars(
        select(T_Order)
        .where(T_Order.parent_order_id.in_(order_actual_list))
    ).all()
    # 计算实际费用和
    order_actual_sum = sum(
        (order.actual_fee_received / Decimal('100')) - (Decimal('2') * order.travel_cost)
        for order in orders_actual
    )
    if order_sum != 0:
        # 加钟总金额
        extend_orders_actual_sum = sum(
            (orders_actual.actual_fee_received or 0) / 100 - 2 * orders_actual.travel_cost
            for orders_actual in extend_orders_actual
        )
        actual_extend_rate_ratio = extend_orders_actual_sum / order_actual_sum
        actual_extend_rate_ratio = round(actual_extend_rate_ratio, 4)
    return {
        "total_order_count": total_order_count,
        "extend_rate_ratio": extend_rate_ratio,
        "actual_total_order_count": actual_total_order_count,
        "actual_extend_rate_ratio": actual_extend_rate_ratio
    }
    