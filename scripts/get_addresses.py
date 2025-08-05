import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta, date, time
import random
from typing import List
from sqlalchemy import and_, desc, distinct, func, or_, text
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
from app.model.t_client_user_position import T_Client_User_Position
from app.model.t_wechat_event import T_Wechat_Events
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

exclude_openids = [
    "oK9p06eiEk0jWNvowVjb5lGlkocM",
    "oK9p06S43s67ui0VxR3-h3REu0VY",
    "oK9p06UX2a02_b9Cn4W7cfoWjE3c",
    # cheng-dianxin
    "oK9p06dxisAkfHLgD-vZIUFmypAg",
]
datetime_str = "2025-05-01"
datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d")


def get_address_from_orders():
    with Session(engine) as session:

        addresses = session.exec(
            select(distinct(T_Order.service_address)).where(
                T_Order.create_order_time > datetime_obj,
                T_Order.service_city == "杭州市",
                T_Order.client_user_id.not_in(exclude_openids),
            )
        ).all()
        print(addresses)
        return addresses


def get_address_from_positions():
    with Session(engine) as session:
        addresses = session.exec(
            select(distinct(T_Client_User_Position.address)).where(
                T_Client_User_Position.refresh_time > datetime_obj,
                T_Client_User_Position.city == "杭州市",
                T_Client_User_Position.client_openid.not_in(exclude_openids),
            )
        ).all()
        return addresses


if __name__ == "__main__":
    address_from_orders = get_address_from_orders()
    address_from_positions = get_address_from_positions()
    print(address_from_orders)
    # export address_from_orders_into csv
    with open("scripts/position_analysis/address_from_orders.csv", "w") as f:
        for address in address_from_orders:
            f.write(address + "\n")

    print(address_from_positions)
    # export address_from_positions_into csv
    with open("scripts/position_analysis/address_from_positions.csv", "w") as f:
        for address in address_from_positions:
            f.write(address + "\n")
