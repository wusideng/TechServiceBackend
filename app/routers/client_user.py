#  订单信息

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple

from app.core.database import engine, get_session
from app.core.util import generate_sms_code
from app.model.q_Sms import SendSmsVerificationCodeRequest, UpdateUserPhoneRequest
from app.model.t_client_user import T_Client_User
from app.model.t_client_user_position import T_Client_User_Position
from app.model.t_sms_code import T_Sms_Code
from app.model.t_user_track import T_User_Track
from app.model.t_wechat_event import T_Wechat_Events
from app.routers.coupon import take_new_user_coupons
from app.routers.voice_sms_hywx import send_sms
from logger import logger


router = APIRouter(
    prefix="/clientUser",
    tags=["clientUser"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/clientListFromCityMangaer")
def get_client_list_from_citymanager(
    pageNumber: int = 1,
    pageSize: int = 10,
    orderBy: str = "create_time",
    session=Depends(get_session),
):
    main_query, count_query = get_main_query(pageNumber, pageSize, orderBy)

    results = session.exec(main_query).all()

    count = session.exec(count_query).first()
    response = []
    user_openids = [res[0].openid for res in results]
    recent_tracks = get_recent_tracks_for_users(session, user_openids, 10)

    # 按用户分组tracks
    tracks_by_user = {}
    for track in recent_tracks:
        if track.user_openid not in tracks_by_user:
            tracks_by_user[track.user_openid] = []
        tracks_by_user[track.user_openid].append(track)
    # 赋值给用户
    for res in results:
        user = res[0]
        address = res[1]
        city = res[2]
        lon = res[3]
        lat = res[4]
        follow_channel = res[5]
        user_dict = user.model_dump()
        user_dict["position"] = {
            "address": address,
            "city": city,
            "lon": lon,
            "lat": lat,
        }
        user_dict["follow_channel"] = follow_channel
        user_dict["tracks"] = tracks_by_user.get(user.openid, [])
        user_dict["tracks"] = [track.model_dump() for track in user_dict["tracks"]]
        response.append(user_dict)
    response_final = {
        "totalCount": count,
        "data": response,
        "currentPage": pageNumber,
        "pageSize": pageSize,
    }
    return response_final


# @router.get("/new_client")
# async def read_client_users_new(pageNum: int = 0, pageSize: int = 10):
#     with Session(engine) as session:
#         offset = pageNum * pageSize
#         total_count = session.exec(select(T_Client_User)).all()
#         total_count = len(total_count)
#         # 子查询获取每个用户的最新位置
#         latest_position_subquery = (
#             select(
#                 T_Client_User_Position.client_openid,
#                 func.max(T_Client_User_Position.refresh_time).label(
#                     "latest_refresh_time"
#                 ),
#             )
#             .group_by(T_Client_User_Position.client_openid)
#             .subquery()
#         )
#         # 连接最新位置
#         statement = (
#             select(T_Client_User, T_Client_User_Position)
#             .outerjoin(
#                 latest_position_subquery,
#                 T_Client_User.openid == latest_position_subquery.c.client_openid,
#             )
#             .outerjoin(
#                 T_Client_User_Position,
#                 (
#                     T_Client_User_Position.client_openid
#                     == latest_position_subquery.c.client_openid
#                 )
#                 & (
#                     T_Client_User_Position.refresh_time
#                     == latest_position_subquery.c.latest_refresh_time
#                 ),
#             )
#             .order_by(T_Client_User.user_id.desc())
#             .offset(offset)
#             .limit(pageSize)
#         )
#         try:
#             results = session.exec(statement).all()
#         except Exception as e:
#             print("Error executing query:", e)
#         data = []
#         for user, position in results:
#             user_data = user.dict()
#             if position:
#                 position_data = {
#                     "lon": position.lon,
#                     "lat": position.lat,
#                     "address": position.address,
#                     "city": position.city,
#                     "detail_address": position.detail_address,
#                 }
#             else:
#                 position_data = None

#             user_data["position"] = position_data
#             data.append(user_data)

#         return {
#             "total_count": total_count,
#             "data": data,
#             "page": pageNum,
#             "page_size": pageSize,
#             "total_pages": (total_count // pageSize)
#             + (1 if total_count % pageSize > 0 else 0),
#         }


# @router.get("/active_client")
# async def read_client_users_active(pageNum: int = 0, pageSize: int = 10):
#     with Session(engine) as session:
#         offset = pageNum * pageSize
#         # 子查询获取每个用户的最新位置
#         latest_position_subquery = (
#             select(
#                 T_Client_User_Position.client_openid,
#                 func.max(T_Client_User_Position.refresh_time).label(
#                     "latest_refresh_time"
#                 ),
#             )
#             .group_by(T_Client_User_Position.client_openid)
#             .subquery()
#         )
#         # 连接最新位置
#         statement = (
#             select(T_Client_User, T_Client_User_Position)
#             .outerjoin(
#                 latest_position_subquery,
#                 T_Client_User.openid == latest_position_subquery.c.client_openid,
#             )
#             .outerjoin(
#                 T_Client_User_Position,
#                 (
#                     T_Client_User_Position.client_openid
#                     == latest_position_subquery.c.client_openid
#                 )
#                 & (
#                     T_Client_User_Position.refresh_time
#                     == latest_position_subquery.c.latest_refresh_time
#                 ),
#             )
#             .order_by(latest_position_subquery.c.latest_refresh_time.desc())
#             .offset(offset)
#             .limit(pageSize)
#         )
#         try:
#             results = session.exec(statement).all()
#             print("all-client:", total_count)  # 确保在这里打印
#         except Exception as e:
#             print("Error executing query:", e)
#         data = []
#         for user, position in results:
#             user_data = user.dict()
#             if position:
#                 position_data = {
#                     "lon": position.lon,
#                     "lat": position.lat,
#                     "address": position.address,
#                     "city": position.city,
#                     "detail_address": position.detail_address,
#                     "refresh_time": position.refresh_time,
#                 }
#                 user_data["position"] = position_data
#                 data.append(user_data)
#             else:
#                 position_data = None
#         total_count = len(data)
#         print("active-client:", total_count)  # 确保在这里打印
#         return {
#             "total_count": total_count,
#             "data": data,
#             "page": pageNum,
#             "page_size": pageSize,
#             "total_pages": (total_count // pageSize)
#             + (1 if total_count % pageSize > 0 else 0),
#         }


@router.get("/{user_id}")
async def read_client_user(user_id: str):
    with Session(engine) as session:
        statement = select(T_Client_User).where(T_Client_User.user_id == user_id)
        results = session.exec(statement)
        return results.first()


@router.get("/client_user_info/user_info")
async def read_client_user_info_by_openid(
    request: Request, session: Session = Depends(get_session)
):
    cookies = request.cookies
    openid = cookies.get("openid")
    assert openid is not None, "no openid found in cookies"

    # 创建单一查询，使用LEFT JOIN获取用户信息和关注列表
    statement = select(
        T_Client_User,
    ).where(T_Client_User.openid == openid)

    # 执行查询
    user = session.exec(statement).first()
    assert user is not None, "no user found"
    result = user.model_dump()
    return result


@router.post("/")
async def create_client_user(client_user: T_Client_User):
    try:
        with Session(engine) as session:
            existing_client_user = session.exec(
                select(T_Client_User).where(
                    T_Client_User.user_id == client_user.user_id
                )
            ).first()
            if existing_client_user:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(client_user)
                session.commit()
                session.refresh(client_user)
                return {"msg": "create sucess", "data": client_user}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_client_user(user_id: int, client_user_info: T_Client_User):
    with Session(engine) as session:
        statement = select(T_Client_User).where(T_Client_User.user_id == user_id)
        result = session.exec(statement)
        client_user = result.one()
        client_user.user_id = client_user_info.user_id
        client_user.user_nickname = client_user_info.user_nickname
        client_user.user_phone = client_user_info.user_phone
        session.add(client_user)
        session.commit()
        session.refresh(client_user)
        return client_user


# 修改客户手机号
@router.post("/update_phone/")
async def update_client_user_phone(
    params: UpdateUserPhoneRequest,
    session: Session = Depends(get_session),
):
    try:
        user_openid = params.user_openid
        phone = params.phone
        code = params.code
        statement = select(T_Client_User).where(T_Client_User.openid == user_openid)
        user = session.exec(statement).first()
        old_phone_number = user.user_phone
        is_new_user = False
        if (
            old_phone_number is None
            or old_phone_number == ""
            or old_phone_number == "string"
        ):
            is_new_user = True
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if code:
            statement = select(T_Sms_Code).where(
                T_Sms_Code.phone == phone,
                T_Sms_Code.expire_time <= datetime.now(),  # 已过期的
            )
            expired_codes = session.exec(statement).all()
            for expired_code in expired_codes:
                session.delete(expired_code)
            # 验证验证码是否正确
            statement = select(T_Sms_Code).where(
                T_Sms_Code.phone == phone,
                T_Sms_Code.code == code,
                T_Sms_Code.is_used == False,
                T_Sms_Code.expire_time > datetime.now(),
            )
            sms_code = session.exec(statement).first()
            if not sms_code:
                session.commit()
                raise HTTPException(status_code=400, detail="验证码错误或已过期")
            session.delete(sms_code)
        # 更新 user_phone 字段
        user.user_phone = phone
        if is_new_user:
            take_new_user_coupons(user_openid, session)
        session.commit()
        session.refresh(user)
        # return user
        user = user.model_dump()
        user["is_new_user"] = is_new_user
        return user
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/send_sms_for_phone_validation/")
async def send_sms_for_phone_validation(
    params: SendSmsVerificationCodeRequest, session: Session = Depends(get_session)
):
    phone_number = params.phone
    user_openid = params.user_openid
    # 验证手机号格式
    if not phone_number or len(phone_number) != 11 or not phone_number.startswith("1"):
        raise HTTPException(status_code=400, detail="手机号格式错误")
    # 检查发送频率限制（60秒内只能发送一次）
    now = datetime.now()
    statement = select(T_Sms_Code).where(
        T_Sms_Code.phone == phone_number,
        T_Sms_Code.create_time > now - timedelta(seconds=60),
    )
    last_sms = session.exec(statement).first()

    if last_sms:
        raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")

    # 生成验证码
    code = generate_sms_code()
    expire_time = now + timedelta(minutes=5)  # 5分钟有效期

    # 清除该手机号之前未使用的验证码
    statement = select(T_Sms_Code).where(
        T_Sms_Code.phone == phone_number, T_Sms_Code.is_used == False
    )
    old_codes = session.exec(statement).all()
    for old_code in old_codes:
        session.delete(old_code)

    # 存储新验证码
    sms_code = T_Sms_Code(phone=phone_number, code=code, expire_time=expire_time)
    session.add(sms_code)
    session.commit()

    # 发送短信
    try:
        text = "尚阳科技提醒您，您的验证码是：{}。请不要把验证码泄露给其他人。".format(
            code
        )
        response = await send_sms(text=text, mobile=phone_number)
        return {
            "type": "verify-code",
            "phone": phone_number,
            "text": text,
            "data": response,
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="验证码发送失败")


# 修改客户邀请码
@router.post("/update_invite_code/")
async def update_client_user_phone(user_id: str, invite_code: str):
    try:
        with Session(engine) as session:
            statement = select(T_Client_User).where(T_Client_User.openid == user_id)
            users = session.exec(statement)
            user = users.first()
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            # 更新 user_phone 字段
            user.invite_code = invite_code
            session.add(user)
            session.commit()
            session.refresh(user)
            # return user
            return {"msg": "update phone success", "data": user}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/del/{user_id}")
async def delete_client_user(user_id: int):
    with Session(engine) as session:
        statement = select(T_Client_User).where(T_Client_User.user_id == user_id)
        results = session.exec(statement)
        client_user = results.first()
        if not client_user:
            return {"msg": "there's no client_user", "data": ""}
        session.delete(client_user)
        session.commit()
        return {"msg": "delete sucess", "data": client_user}


@router.post("/track_user_behavior/")
async def track_user_behavior(
    user_behavior: T_User_Track, session: Session = Depends(get_session)
):
    try:
        session.add(user_behavior)
        session.commit()
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error occurred while tracking user: {str(e)}")


def get_main_query(
    pageNumber,
    pageSize,
    orderBy: str = "create_time",
):

    # 最新track时间子查询
    latest_track_subquery = (
        select(
            T_User_Track.user_openid,
            func.max(T_User_Track.create_time).label("latest_track_time"),
        )
        .group_by(T_User_Track.user_openid)
        .subquery()
    )
    latest_positions_subquery = (
        select(
            T_Client_User_Position,
            func.row_number()
            .over(
                partition_by=T_Client_User_Position.client_openid,
                order_by=[
                    T_Client_User_Position.refresh_time.desc(),  # create_time 最近的优先
                ],
            )
            .label("rn"),
        )
    ).subquery()
    latest_positions = (
        select(latest_positions_subquery).where(latest_positions_subquery.c.rn == 1)
    ).subquery()
    latest_follow_subquery = (
        select(
            T_Wechat_Events,
            func.row_number()
            .over(
                partition_by=T_Wechat_Events.user_openid,
                order_by=T_Wechat_Events.create_time.desc(),  # 或其他时间字段
            )
            .label("rn"),
        ).where(T_Wechat_Events.event_type == "scan_and_follow")
    ).subquery()

    latest_follow = (
        select(latest_follow_subquery).where(latest_follow_subquery.c.rn == 1)
    ).subquery()

    main_query = (
        select(
            T_Client_User,
            latest_positions.c.address,
            latest_positions.c.city,
            latest_positions.c.lon,
            latest_positions.c.lat,
            latest_follow.c.scene_str,
        )
        .outerjoin(
            latest_track_subquery,
            T_Client_User.openid == latest_track_subquery.c.user_openid,
        )
        .outerjoin(
            latest_positions,
            T_Client_User.openid
            == latest_positions.c.client_openid,  # 添加这个关联条件
        )
        .outerjoin(
            latest_follow,
            T_Client_User.openid == latest_follow.c.user_openid,  # 添加这个关联条件
        )
    )
    count_query = select(func.count()).select_from(main_query.alias())

    if pageNumber is not None and pageSize is not None:
        try:
            # 计算偏移量
            offset_value = (pageNumber - 1) * pageSize
            # 应用limit和offset
            main_query = main_query.limit(pageSize).offset(offset_value)
        except (ValueError, TypeError):
            # 如果pageNumber或pageSize不是有效的整数，则不应用分页
            pass
    # 按照用户注册时间排序
    if orderBy == "create_time":
        main_query = main_query.order_by(T_Client_User.user_createtime.desc())
    # 按照用户最近访问的时间排序
    else:
        main_query = main_query.order_by(
            latest_track_subquery.c.latest_track_time.desc()
        )
    return main_query, count_query


def get_recent_tracks_for_users(session, user_openids, limit=10):
    """获取指定用户的最近N条tracks"""
    # 使用窗口函数直接查询T_User_Track
    recent_tracks_query = (
        select(
            T_User_Track,
            func.row_number()
            .over(
                partition_by=T_User_Track.user_openid,
                order_by=T_User_Track.create_time.desc(),
            )
            .label("rn"),
        ).where(T_User_Track.user_openid.in_(user_openids))
    ).subquery()

    # 选择完整的T_User_Track对象
    final_query = (
        select(T_User_Track)
        .where(
            T_User_Track.id.in_(
                select(recent_tracks_query.c.id).where(
                    recent_tracks_query.c.rn <= limit
                )
            )
        )
        .order_by(T_User_Track.user_openid, T_User_Track.create_time.desc())
    )

    result = session.exec(final_query).all()

    return result
