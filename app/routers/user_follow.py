from datetime import datetime, timedelta
from geopy.distance import great_circle
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, func, text
from sqlalchemy.orm import noload, selectinload
from sqlmodel import Session, select
from app.core.database import get_session
from app.lib.utils.sql_query import get_next_worktimes_query
from app.model.t_client_user import T_Client_User
from app.model.t_order_comment import T_Order_Comment
from app.model.t_tech_addresses import TechAddress
from app.model.t_tech_user import T_Tech_User
from typing import List

from app.model.t_tech_user_worktime import T_Tech_User_Worktime
from app.model.t_time_slots import T_Time_Slots
from app.model.t_user_follows import T_User_Follows

router = APIRouter()


class UserFollowRequest(BaseModel):
    user_openid: str
    tech_openid: str


@router.post("/follow")
async def follow_tech(
    params: UserFollowRequest,
    session: Session = Depends(get_session),
):
    user_openid = params.user_openid
    tech_openid = params.tech_openid
    # Check if already following
    existing_follow = session.exec(
        select(T_User_Follows).where(
            T_User_Follows.user_openid == user_openid,
            T_User_Follows.tech_openid == tech_openid,
        )
    ).first()
    assert existing_follow is None, "Already following this techn user"
    # Create new follow
    new_follow = T_User_Follows(user_openid=user_openid, tech_openid=tech_openid)
    session.add(new_follow)
    session.commit()
    return new_follow


@router.post("/unfollow")
async def unfollow_tech(
    params: UserFollowRequest, session: Session = Depends(get_session)
):
    user_openid = params.user_openid
    tech_openid = params.tech_openid
    follow = session.exec(
        select(T_User_Follows).where(
            T_User_Follows.user_openid == user_openid,
            T_User_Follows.tech_openid == tech_openid,
        )
    ).first()
    assert follow is not None, "Not following this tech user"
    session.delete(follow)
    session.commit()
    return {"status": "success", "message": "Technician unfollowed successfully"}


# 用户查询关注的技师列表
@router.get("/following/{user_openid}")
async def get_following_techs(
    user_openid: str,
    lon=None,
    lat=None,
    session: Session = Depends(get_session),
):
    main_query = get_main_query(user_openid, lon, lat)
    results = session.exec(main_query).all()
    response = []
    for result in results:
        user = result[0]  # T_Tech_User 对象
        position_lon = result[1]
        position_lat = result[2]
        position_address = result[3]
        position_work_city = result[4]
        position_refresh_time = result[5]
        approx_distance = result[6]
        worktime_date = result[7]
        worktime_start = result[8]
        worktime_end = result[9]
        follow_count = result[10]

        if position_lat and position_lon and lon and lat:
            distance = great_circle((lat, lon), (position_lat, position_lon)).kilometers
        else:
            distance = 1000
        user_data = {
            "user_id": user.user_id,
            "user_phone": user.user_phone,
            "user_nickname": user.user_nickname,
            "user_sex": user.user_sex,
            "user_age": user.user_age,
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
            "tech_user_id": user.openid if position_lon else None,
            "lon": position_lon if position_lon else 120.1,
            "lat": position_lat if position_lat else 30.1,
            "address": position_address,
            "work_city": position_work_city,
            "refresh_time": position_refresh_time,
            "distance": distance,
            "worktime": worktime_start,
            "workdate": worktime_date,
            "follow_count": follow_count,
        }
        response.append(user_data)
    return response


# 技师查询关注她的用户列表
@router.get("/followers/{tech_openid}")
async def get_followers(tech_openid: str, session: Session = Depends(get_session)):
    result = session.exec(
        select(T_Client_User)
        .join(T_User_Follows, T_Client_User.openid == T_User_Follows.user_openid)
        .where(T_User_Follows.tech_openid == tech_openid)
        .order_by(desc(T_User_Follows.create_time))
    ).all()
    return result


def get_main_query(user_openid: str, lon: float, lat: float):
    current_time = datetime.now()
    current_date = current_time.date()
    # 最新位置子查询
    latest_positions_subquery = (
        select(
            TechAddress.openid,
            TechAddress.lon,
            TechAddress.lat,
            TechAddress.address,
            TechAddress.city,
            TechAddress.create_time,
            # 使用数据库函数直接计算距离(PostgreSQL)
            func.sqrt(
                func.power(TechAddress.lon - lon, 2)
                + func.power(TechAddress.lat - lat, 2)
            ).label(
                "approx_distance"
            ),  # 近似距离用于排序
            func.row_number()
            .over(
                partition_by=TechAddress.openid,
                order_by=[
                    TechAddress.is_default.desc(),  # is_default=True 优先
                    TechAddress.create_time.desc(),  # create_time 最近的优先
                ],
            )
            .label("rn"),
        )
    ).subquery()

    latest_positions = (
        select(latest_positions_subquery).where(latest_positions_subquery.c.rn == 1)
    ).subquery()
    tomorrow = datetime.now() + timedelta(days=1)

    # 下一个工作时间子查询
    next_worktimes_subquery = get_next_worktimes_query()

    next_worktimes = (
        select(next_worktimes_subquery).where(next_worktimes_subquery.c.rn == 1)
    ).subquery()

    # 添加关注计数子查询
    follow_count_subquery = (
        select(
            T_User_Follows.tech_openid,
            func.count(T_User_Follows.id).label("follow_count"),
        ).group_by(T_User_Follows.tech_openid)
    ).subquery()

    # comment_count_expr = (
    #     select(func.count(T_Order_Comment.order_comment_id))
    #     .where(T_Order_Comment.tech_id == T_Tech_User.openid)
    #     .scalar_subquery()
    #     .label("comment_count")
    # )
    # 主查询
    main_query = (
        select(
            T_Tech_User,
            latest_positions.c.lon,
            latest_positions.c.lat,
            latest_positions.c.address,
            latest_positions.c.city,
            latest_positions.c.create_time,
            latest_positions.c.approx_distance,
            next_worktimes.c.work_date,
            next_worktimes.c.start_time,
            next_worktimes.c.end_time,
            follow_count_subquery.c.follow_count,
            # comment_count_expr
        )
        .options(
            noload(T_Tech_User.orders),
        )
        .join(T_User_Follows, T_Tech_User.openid == T_User_Follows.tech_openid)
        .outerjoin(latest_positions, T_Tech_User.openid == latest_positions.c.openid)
        .outerjoin(next_worktimes, T_Tech_User.openid == next_worktimes.c.tech_user_id)
        .outerjoin(
            follow_count_subquery,
            T_Tech_User.openid == follow_count_subquery.c.tech_openid,
        )
        .where(T_User_Follows.user_openid == user_openid)
        .order_by(T_User_Follows.create_time.desc())
    )
    return main_query
