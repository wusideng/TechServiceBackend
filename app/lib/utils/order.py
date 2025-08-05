#  订单信息

from sqlalchemy import func
from sqlmodel import select
from app.model.t_order import T_Order
from app.core.config import action_status_code_dict


def get_all_todo_orders_count_func(session):
    statement: int = select(func.count(T_Order.order_id)).where(
        (
            T_Order.payment_status_code
            == action_status_code_dict.get("client").get("paid").get("code")
        )
        & (
            (T_Order.order_status_code_tech.is_(None))  # 添加NULL值判断
            | (
                T_Order.order_status_code_tech  # 使用OR连接两个条件
                != action_status_code_dict.get("tech").get("has_left").get("code")
            )
        )
        & (T_Order.parent_order_id.is_(None))
    )

    order_count = session.exec(statement).first()
    return order_count


def get_todo_orders_count_by_userid_func(user_id, session):
    statement: int = select(func.count(T_Order.order_id)).where(
        (T_Order.tech_user_id == user_id)
        & (
            T_Order.payment_status_code
            == action_status_code_dict.get("client").get("paid").get("code")
        )
        & (
            (T_Order.order_status_code_tech.is_(None))  # 添加NULL值判断
            | (
                T_Order.order_status_code_tech  # 使用OR连接两个条件
                != action_status_code_dict.get("tech").get("has_left").get("code")
            )
        )
        & (T_Order.parent_order_id.is_(None))
    )
    order_count = session.exec(statement).first()
    return order_count
