#  订单信息

from sqlalchemy import and_, desc, func, or_
from sqlmodel import Session, select

from app.model.t_order import T_Order
from app.core.config import action_status_code_dict

# 渠道费（平台维护费）
maintainence_fee = 10
# 提现手续费
withdraw_fee = 5
# 技师提成百分比（默认分成比例，当技师分成比例未设置则使用 70%）
default_ratio = 70

def calculate_benefit_for_order(order: T_Order, session: Session):
    order_id = order.order_id
    orders = session.exec(
        select(
            T_Order.order_id,
            T_Order.order_cost,
            T_Order.travel_cost,
        ).where(
            or_(T_Order.order_id == order_id, T_Order.parent_order_id == order_id),
            T_Order.payment_status_code
            == action_status_code_dict["client"]["paid"]["code"],
        )
    ).all()
    total_fee_paid_by_customer = sum([order.order_cost for order in orders])
    tech_benefit = 0
    for o in orders:
        if o.order_id != order.order_id:
            current_withdraw_fee = 0
        else:
            current_withdraw_fee = withdraw_fee
        ratio = order.tech.ratio
        if ratio is None:
            ratio = default_ratio
        tech_benefit += (
            (o.order_cost - o.travel_cost * 2) * ratio / 100
            - maintainence_fee
            - current_withdraw_fee
            + o.travel_cost * 2
        )
    return [total_fee_paid_by_customer, tech_benefit]
