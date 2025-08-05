import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta, date, time
from typing import List
from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import (
    contains_eager,
    joinedload,
    noload,
    selectinload,
    with_loader_criteria,
)
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import action_status_code_dict

from app.model.t_order import T_Order
from app.model.t_client_user import T_Client_User
from app.model.t_order_comment import T_Order_Comment
from app.model.t_order_product import T_Order_Product
from app.model.t_order_status import T_Order_Status
from app.model.t_product import T_Product
from app.model.t_tech_busy_time import T_Tech_Busy_Time
from app.model.t_tech_user import T_Tech_User
from app.model.t_time_slots import T_Time_Slots
from app.model.t_user_follows import T_User_Follows
from app.routers.tech_user import T_Tech_User_Worktime, get_main_query
from sqlalchemy import func, cast, Date

calculate_today = False
# 交税百分比
tax_rate = 0.06
# 提现手续费
withdraw_fee = 5
# 技师提成百分比
tech_benefit_rate = 0.7
# 渠道费（平台维护费）
maintenance_fee = 18

techs = {}
actual_travel_fees = {}


def set_actual_travel_fee(order_id: str, actual_travel_fee: float):
    actual_travel_fees[order_id] = actual_travel_fee


# [{"order_id":1, "actual_travel_fee": 100}]
def set_actual_travel_fees(actual_travel_fees: List[dict]):
    if actual_travel_fees is None:
        return
    for actual_travel_fee in actual_travel_fees:
        set_actual_travel_fee(
            actual_travel_fee["order_id"], actual_travel_fee["actual_travel_fee"]
        )


def main(order_ids: List[int], actual_travel_fees: List[dict] = None):
    set_actual_travel_fees(actual_travel_fees)

    with Session(engine) as session:
        statement = (
            select(T_Order)
            .options(selectinload(T_Order.tech))
            .where(
                T_Order.payment_status_code
                == action_status_code_dict["client"]["paid"]["code"],
                T_Order.order_id.in_(order_ids),
            )
        )
        orders = session.exec(statement).all()
        sum_for_all_techs = {}
        for order in orders:
            tech_name = order.tech.user_nickname
            benefit_info = calculate_benefit(order, session)
            if tech_name not in sum_for_all_techs:
                sum_for_all_techs[tech_name] = [benefit_info]
            else:
                sum_for_all_techs[tech_name].append(benefit_info)
            print(f"-------------------------------")
            # print(f"{order.tech.user_nickname}第{index+1}单")
            print(f"订单编号：{benefit_info['order_id']}")
            print(
                f"下单时间：{benefit_info['create_order_time'].strftime('%Y-%m-%d %H:%M')}"
            )
            print(f"技师姓名：{tech_name}")
            print(f"订单总价：{benefit_info['order_cost']}")
            print(f"平台预估车费：{benefit_info['travel_fee']}")
            print(f"实际车费：{benefit_info['actual_travel_fee']}")
            print(f"渠道费：{maintenance_fee}")
            print(f"手续费：{benefit_info['withdraw_fee']}")
            print("\n")
            print(
                f"技师收益：({benefit_info['order_cost']}-{benefit_info['travel_fee']})*{tech_benefit_rate}-{maintenance_fee}-{benefit_info['withdraw_fee']}+{benefit_info['actual_travel_fee']} = {benefit_info['tech_benefit']}"
            )
            print(
                f"上缴税收：{benefit_info['order_cost']}*{tax_rate}={benefit_info['total_tax_cost']}"
            )
            print(
                f"平台收益：{benefit_info['order_cost']}-{benefit_info['tech_benefit']}-{benefit_info['total_tax_cost']}={benefit_info['platform_benefit']}"
            )
        print("\n")

        for tech_name in sum_for_all_techs:
            print(tech_name)
            benefit_infos = sum_for_all_techs[tech_name]
            tech_sum_benefit = round(
                sum([benefit_info["tech_benefit"] for benefit_info in benefit_infos]),
                2,
            )
            tax_sum = round(
                sum([benefit_info["total_tax_cost"] for benefit_info in benefit_infos]),
                2,
            )
            platform_sum_benefit = round(
                sum(
                    [benefit_info["platform_benefit"] for benefit_info in benefit_infos]
                ),
                2,
            )
            print(f"技师{tech_name}总收益:{tech_sum_benefit}")
            # print(f"技师订单总上缴税收:{tax_sum}")
            # print(f"技师订单平台总收益:{platform_sum_benefit}")


def get_benefit_info(
    order_cost,
    travel_fee,
    actual_travel_fee,
    withdraw_fee_for_current_order,
    tech_name,
    order_id,
    create_order_time,
):
    order_cost = float(order_cost)
    tax_fee = order_cost * tax_rate
    tech_benefit = (
        (order_cost - travel_fee) * tech_benefit_rate
        - withdraw_fee_for_current_order
        - maintenance_fee
        + actual_travel_fee
    )
    total_tax_cost = tax_fee
    platform_benefit = order_cost - total_tax_cost - tech_benefit
    benefit_info = {
        "order_cost": order_cost,
        "travel_fee": travel_fee,
        "actual_travel_fee": actual_travel_fee,
        "tax_fee": tax_fee,
        "withdraw_fee": withdraw_fee_for_current_order,
        "tech_name": tech_name,
        "tech_benefit": tech_benefit,
        "total_tax_cost": total_tax_cost,
        "platform_benefit": platform_benefit,
        "order_id": order_id,
        "create_order_time": create_order_time,
    }
    for key in benefit_info:
        if type(benefit_info[key]) != str and type(benefit_info[key]) != datetime:
            benefit_info[key] = round(benefit_info[key], 2)
    return benefit_info


def calculate_benefit(order: T_Order, session: Session):
    tech: T_Tech_User = order.tech
    order_id = order.order_id
    # sub_order_statement = select(T_Order).where(T_Order.parent_order_id == order_id)
    # sub_orders = session.exec(sub_order_statement).all()
    tech_name = tech.user_nickname
    # 订单总费用,包含加钟订单
    # order_cost = float(
    #     order.order_cost + sum([sub_order.order_cost for sub_order in sub_orders])
    # )
    order_cost = float(order.order_cost)
    travel_fee = float(order.travel_cost * 2)
    # tax_fee = order_cost * tax_rate
    withdraw_fee_for_current_order = 0 if tech_name in techs else withdraw_fee
    techs[tech_name] = True
    actual_travel_fee = (
        actual_travel_fees[order_id] if order_id in actual_travel_fees else travel_fee
    )
    if order.parent_order_id:
        travel_fee = 0
        actual_travel_fee = 0
    benefit_info = get_benefit_info(
        order_cost,
        travel_fee,
        actual_travel_fee,
        withdraw_fee_for_current_order,
        tech_name,
        order_id,
        order.create_order_time,
    )

    return benefit_info


if __name__ == "__main__":
    order_ids = [251]
    main(order_ids)
