#  模拟技师
import os
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import Session, select, not_, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy import case, text

from geopy.distance import great_circle
from datetime import datetime, date, timedelta

from app.core.database import engine
from app.lib.utils.upload import upload_file_to_cdn
from app.model.t_tech_user import T_Tech_User
from app.model.t_tech_user_position import T_Tech_User_Position
from app.model.t_tech_user_worktime import T_Tech_User_Worktime
from app.model.t_time_slots import T_Time_Slots

router = APIRouter(
    prefix="/techUserMock",
    tags=["techUserMock"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


# 查看机器人技师基本信息列表（管理端）
# @router.get("/Techs")
# async def read_tech_users():
#     with Session(engine) as session:
#         statement = (
#             select(T_Tech_User)
#             .where(T_Tech_User.openid.like("%mock%"), T_Tech_User.openid.like("%Mock%"))
#             .order_by(T_Tech_User.user_id)
#         )
#         users = session.exec(statement).all()
#         return users


# 查看机器人技师时间列表（管理端）
@router.get("/TechsWorktime")
async def read_tech_users_worktime():
    with Session(engine) as session:
        statement = (
            select(T_Tech_User)
            .where(T_Tech_User.openid.like("%mock%"), T_Tech_User.openid.like("%Mock%"))
            .order_by(T_Tech_User.user_id)
        )
        users = session.exec(statement).all()
        # tech_users = users.scalars().all()
        response = []
        for user in users:
            # 计算技师最近的工作时间
            # 查询技师的工作时间段
            current_time = datetime.now()
            worktime = (
                select(T_Tech_User_Worktime, T_Time_Slots)
                .join(
                    T_Time_Slots, T_Tech_User_Worktime.slot_id == T_Time_Slots.slot_id
                )
                .where(
                    T_Tech_User_Worktime.tech_user_id == user.openid,
                    text(
                        """
                            CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                            CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) > :current_time
                        """
                    ).bindparams(current_time=current_time),
                )
                .order_by(
                    T_Tech_User_Worktime.work_date, T_Time_Slots.start_time
                )  # 按开始时间排序
            )
            worktime_results = session.exec(worktime).all()
            # 获取第一个符合条件的工作时间段
            if worktime_results:
                first_schedule = worktime_results[0]  # 获取第一个工作时间段
                tech_user_worktime = first_schedule[
                    0
                ]  # 第一个元素为 T_Tech_User_Worktime
                time_slot = first_schedule[1]  # 第二个元素为 T_Time_Slots
                print(
                    f"Next work time for tech user {user.openid}: "
                    f"{time_slot.start_time} to {time_slot.end_time}"
                )
                start_time = time_slot.start_time
                end_time = time_slot.end_time
                worktime_date = tech_user_worktime.work_date
            else:
                print("No upcoming work time found.")
                start_time = None
                worktime_date = None
                end_time = None  # 修复方式：在else分支中初始化end_time为None

            user_data = {
                "user_id": user.user_id,
                "user_phone": user.user_phone,
                "user_nickname": user.user_nickname,
                "user_sex": user.user_sex,
                "user_age": user.user_age,
                "user_city": user.user_city,
                "idnetity_card": user.idnetity_card,
                "openid": user.openid,
                "headimgurl": user.headimgurl,
                "work_phone": user.work_phone,
                "bank_card_id": user.bank_card_id,
                "bank_card_type": user.bank_card_type,
                "user_desc": user.user_desc,
                "photo_work": user.photo_work,
                "photo_life_1": user.photo_life_1,
                "photo_life_2": user.photo_life_2,
                "photo_life_3": user.photo_life_3,
                "worktime": start_time,
                "workdate": worktime_date,
                # 可以添加其他字段
            }
            response.append(user_data)
            # 根据最近工作时间排序
            response.sort(key=lambda x: (x["worktime"] is None, x["worktime"]))
            # 根据最近工作距离排序
        return response


# 查看机器人技师位置信息列表（管理端）
@router.get("/TechsPosition")
async def read_tech_users():
    with Session(engine) as session:
        statement = (
            select(T_Tech_User)
            .where(T_Tech_User.openid.like("%mock%"), T_Tech_User.openid.like("%Mock%"))
            .order_by(T_Tech_User.user_id)
        )
        users = session.exec(statement).all()  # 获取所有用户
        response = []
        for user in users:  # 直接遍历 users 列表
            position_query = (
                select(T_Tech_User_Position)
                .where(T_Tech_User_Position.tech_user_id == user.openid)
                .order_by(T_Tech_User_Position.refresh_time.desc())
                .limit(1)
            )
            position_result = session.execute(position_query)
            latest_position = position_result.scalar_one_or_none()
            user_data = {
                "user_id": user.user_id,
                "user_phone": user.user_phone,
                "user_nickname": user.user_nickname,
                "user_sex": user.user_sex,
                "user_age": user.user_age,
                "user_city": user.user_city,
                "idnetity_card": user.idnetity_card,
                "openid": user.openid,
                "headimgurl": user.headimgurl,
                "work_phone": user.work_phone,
                "bank_card_id": user.bank_card_id,
                "bank_card_type": user.bank_card_type,
                "user_desc": user.user_desc,
                "photo_work": user.photo_work,
                "photo_life_1": user.photo_life_1,
                "photo_life_2": user.photo_life_2,
                "photo_life_3": user.photo_life_3,
                "tech_user_id": (
                    latest_position.tech_user_id if latest_position else None
                ),
                "lon": latest_position.lon if latest_position else 120.1,
                "lat": latest_position.lat if latest_position else 30.1,
                "address": latest_position.address if latest_position else None,
                "work_city": latest_position.work_city if latest_position else None,
                "refresh_time": (
                    latest_position.refresh_time if latest_position else None
                ),
            }
            response.append(user_data)
        return response
