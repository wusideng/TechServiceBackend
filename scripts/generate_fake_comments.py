import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta, date, time
import random
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

tech_name_openid_map = {
    "HangzhouMocka": "杨晓丽",
    "HangzhouMockb": "刘一艳",
    "HangzhouMockc": "李媛媛",
    "HangzhouMockd": "邹淇悦",
    "HangzhouMocke": "何晓晓",
    "HangzhouMockf": "陈雅丽",
    "HangzhouMockg": "赵美琳",
    "HangzhouMockh": "张如初",
}
fake_tech_openids = [
    "HangzhouMocka",
    "HangzhouMockb",
    "HangzhouMockc",
    "HangzhouMockd",
    "HangzhouMocke",
    "HangzhouMockf",
    "HangzhouMockg",
    "HangzhouMockh",
]


def get_tech_by_openid(tech_openid):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.openid == tech_openid)
        tech_user = session.exec(statement).first()
        return tech_user


# 定义一个函数，生成一个随机数
def generate_random_number(max):
    # 使用randint函数生成一个1到max之间的随机数
    return random.randint(1, max) - 1


def generate_random_numbers(max, count):
    result = []
    for i in range(count):
        random_number = generate_random_number(max)
        while random_number in result:
            random_number = generate_random_number(max)
        result.append(random_number)
    return result


def generate_comment():
    comment_options = ["非常棒", "非常专业", "相当专业", "服装整洁", "热情礼貌"]
    random_numbers = generate_random_numbers(len(comment_options), 3)
    random_numbers.sort()
    return "，".join([comment_options[i] for i in random_numbers])


def generate_fake_tech_openids():
    random_numbers = generate_random_numbers(len(fake_tech_openids), 2)
    return [fake_tech_openids[i] for i in random_numbers]


def generate_comments(datetime_strs, tech_openids=[]):
    assert datetime_strs != [], "datetimes should not be empty"
    assert datetime_strs is not None, "datetime should not be None"
    if tech_openids == []:
        tech_openids = generate_fake_tech_openids()
    for index, tech_openid in enumerate(tech_openids):
        comment = generate_comment()
        comment_time = datetime.strptime(datetime_strs[index], "%Y-%m-%d %H:%M:%S")
        tech_user = get_tech_by_openid(tech_openid)
        if tech_user:
            with Session(engine) as session:
                new_order = T_Order(
                    service_time=datetime.now(),
                    payment_status=action_status_code_dict["client"][
                        "wait_for_payment"
                    ]["text"],
                    payment_status_code=action_status_code_dict["client"][
                        "wait_for_payment"
                    ]["code"],
                    service_address="fake_address",
                    service_city="fake_city",
                    service_detail_address="fake_detail_address",
                    travel_distance=0,
                    travel_cost=0,
                    client_user_id="fake_client_user_id",
                    tech_user_id=tech_openid,
                    order_cost=0,
                )
                session.add(new_order)
                tech_comment = T_Order_Comment(
                    order_id=new_order.order_id,
                    client_comment_time=comment_time,
                    client_score_to_tech=5,
                    client_openid=new_order.client_user_id,
                    tech_id=new_order.tech_user_id,
                    client_comment=comment,
                )
                session.add(tech_comment)
                print("----------------------------------------------")
                print("技师姓名：", tech_user.user_nickname)
                print("技师openid：", tech_openid)
                print("顾客评论：", comment)
                print("顾客评论技师时间：", comment_time)
                session.commit()


def main():
    # 随机挑选两个机器人技师评论
    new_datetime_str1 = "2025-05-30 05:32:22"
    new_datetime_str2 = "2025-05-30 07:13:52"
    datetime_strs = [new_datetime_str1, new_datetime_str2]
    generate_comments(datetime_strs)


if __name__ == "__main__":

    main()
