#  订单信息
from decimal import Decimal
from sqlalchemy import and_, desc, func, or_
from sqlmodel import Session, select

from app.model.t_order import T_Order
from app.core.config import action_status_code_dict

# 渠道费（平台维护费）（营业税）
maintainence_fee = 10
# 提现手续费
withdraw_fee = 5
# 技师提成百分比（默认分成比例，当技师分成比例未设置则使用 70%，加钟订单按照70%计算）
default_ratio = 70
tech_benefit_rate_add = 70
# 交税百分比
tax_rate = Decimal('0.06')

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
        # 加钟订单提现手续费 0 , 非加钟订单提现手续费 5
        if o.order_id != order.order_id:
            current_withdraw_fee = 0
        else:
            current_withdraw_fee = withdraw_fee
        ratio = order.tech.ratio
        if ratio is None:
            ratio = default_ratio

        # 加钟订单技师提成（70%） tech_benefit_rate_add = 70
        if order.parent_order_id:
            ratio = tech_benefit_rate_add
        tech_benefit += (
            (o.order_cost - o.travel_cost * 2) * ratio / 100
            - maintainence_fee
            - current_withdraw_fee
            + o.travel_cost * 2
        )
    tax = tax_rate * total_fee_paid_by_customer
    print(f'total_fee_paid_by_customer: {total_fee_paid_by_customer}, tech_benefit: {tech_benefit}, tax: {tax}')

    return [total_fee_paid_by_customer, tech_benefit, tax]
