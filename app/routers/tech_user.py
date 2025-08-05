#  技师信息
from typing import Optional, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Case, and_, literal, not_, exists, func, or_, text
from sqlalchemy.orm import aliased, noload, selectinload
from app.core.config import action_status_code_dict

from app.core.util import get_latest_available_worktime
from app.lib.utils.sql_query import (
    get_next_worktimes_query,
)
from app.model.q_Sms import InviteHerRequest
from app.model.t_apply_status import T_Apply_Status
from app.model.t_order import T_Order
from app.model.t_order_product import T_Order_Product
from app.model.t_sms_invite import T_Sms_Invite
from app.model.t_tech_busy_time import T_Tech_Busy_Time
from app.model.t_tech_user_contract import T_Tech_USER_Contract
from app.model.t_tech_user_product import T_Tech_User_Product
from geopy.distance import great_circle
from datetime import datetime, timedelta

from app.core.database import engine
from app.lib.utils.upload import upload_file_to_cdn, upload_file_to_local
from app.model.t_tech_user import T_Tech_User
from app.model.t_tech_user_position import T_Tech_User_Position
from app.model.t_tech_user_worktime import T_Tech_User_Worktime
from app.model.t_time_slots import T_Time_Slots
from app.model.t_product import T_Product
from app.core.database import get_session
from app.model.t_order_comment import T_Order_Comment
from app.model.t_user_follows import T_User_Follows
from app.model.t_tech_addresses import TechAddress

from app.routers.voice_sms_hywx import send_sms
from logger import logger

router = APIRouter(
    prefix="/techUser",
    tags=["techUser"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/tech_info/get_initial_values")
async def get_initial_values(
    openid: str, user_id: int, session: Session = Depends(get_session)
):
    default_address_statement = select(TechAddress).where(
        TechAddress.openid == openid, TechAddress.is_default == True
    )
    default_address = session.exec(default_address_statement).first()
    todo_order_count_statement: int = select(func.count(T_Order.order_id)).where(
        (T_Order.tech_user_id == openid)
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
    order_count = session.exec(todo_order_count_statement).first()
    products = session.exec(select(T_Product).order_by(T_Product.price_current)).all()

    tech_products_statment = (
        select(T_Product)
        .select_from(T_Tech_User_Product)
        .join(T_Product, T_Tech_User_Product.product_id == T_Product.product_id)
        .where(T_Tech_User_Product.user_id == user_id)
        .order_by(T_Product.price_current)
    )
    tech_products = session.exec(tech_products_statment).all()
    return {
        "defaultAddress": default_address,
        "todoOrderCount": order_count,
        "products": products,
        "techProducts": tech_products,
    }


@router.get("/get_tech_user_info_from_cookie/tech_info")
def get_tech_user_info_from_cookie(
    request: Request, session: Session = Depends(get_session)
):
    cookies = request.cookies
    openid = cookies.get("openid")
    assert openid is not None, "no openid found in cookies"

    # 创建单一查询，使用LEFT JOIN获取用户信息和关注列表
    statement = select(
        T_Tech_User,
    ).where(T_Tech_User.openid == openid)

    # 执行查询
    user = session.exec(statement).first()
    assert user is not None, "no user found"
    result = user.model_dump()
    statement = select(T_Apply_Status).where(
        T_Apply_Status.tech_id == openid, T_Apply_Status.apply_type == "tech_join"
    )
    statement = (
        select(T_Apply_Status)
        .where(
            T_Apply_Status.tech_id == openid, T_Apply_Status.apply_type == "tech_join"
        )
        .order_by(T_Apply_Status.createTime.desc())
    )
    join_status = session.exec(statement).first()
    result["joinStatus"] = join_status.apply_status if join_status else "unapplied"
    return result


@router.get("/getAllRealTechUsers")
async def read_tech_users(
    user_nickname: str = None,
    session: Session = Depends(get_session),
):
    main_query = (
        select(T_Tech_User)
        .where(
            not_(T_Tech_User.openid.like("%mock%")),
            not_(T_Tech_User.openid.like("%Mock%")),
            T_Tech_User.work_phone != "",
            T_Tech_User.work_phone != "string",
        )
        .order_by(T_Tech_User.user_id.desc())
    )
    if user_nickname:
        main_query = main_query.where(
            T_Tech_User.user_nickname.like(f"%{user_nickname}%")
        )
    users = session.exec(main_query).all()
    return users


# 读取技师列表
@router.get("/techListFromSuperAdmin")
async def read_tech_users_by_super_admin(
    pageNumber: int,
    pageSize: int,
    user_nickname: Optional[str] = None,
    isMock: Optional[bool] = None,
    isOnline: Optional[bool] = None,
    city: Optional[str] = None,
    withPosition: Optional[bool] = None,
    withWorktime: Optional[bool] = None,
    session: Session = Depends(get_session),
):
    select_columns = [T_Tech_User]
    main_query = select(*select_columns)
    print("withPosition", withPosition)
    print("withWorkTime", withWorktime)

    # 如果需要地址信息，JOIN 最新的地址（按创建时间倒序取第一条）
    if withPosition:
        latest_positions_subquery = (
            select(
                TechAddress,
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

        # 先创建过滤后的子查询
        latest_positions = (
            select(latest_positions_subquery).where(latest_positions_subquery.c.rn == 1)
        ).subquery()

        # 然后使用 aliased 创建模型别名
        LatestAddress = aliased(TechAddress, latest_positions)
        select_columns.append(LatestAddress)

    # 如果需要工作时间信息，JOIN 最新的工作时间
    if withWorktime:
        tomorrow = datetime.now() + timedelta(days=1)
        latest_available_time = get_latest_available_worktime()

        next_worktimes_subquery = (
            select(
                T_Tech_User_Worktime,
                T_Time_Slots,
                func.row_number()
                .over(
                    partition_by=T_Tech_User_Worktime.tech_user_id,
                    order_by=[
                        T_Tech_User_Worktime.work_date,
                        T_Tech_User_Worktime.slot_id,
                    ],
                )
                .label("rn"),
            )
            .join(T_Time_Slots, T_Tech_User_Worktime.slot_id == T_Time_Slots.slot_id)
            .outerjoin(
                T_Tech_Busy_Time,
                T_Tech_User_Worktime.tech_user_id == T_Tech_Busy_Time.tech_user_openid,
            )
            .where(
                text(
                    """
                    CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' +
                    CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) > :latest_available_datetime
                    """
                ).bindparams(latest_available_datetime=latest_available_time),
                text(
                    """
                    CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                    CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) < :tomorrow
                    """
                ).bindparams(tomorrow=tomorrow),
                text(
                    """     
                    (
                        t_tech_busy_time.tech_user_openid IS NULL
                        OR
                        (
                            CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                            CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) <= t_tech_busy_time.start_time
                            OR
                            CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                            CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) >= t_tech_busy_time.end_time
                        )
                    )
                    """
                ),
                T_Tech_User_Worktime.active == 1,
            )
        ).subquery()

        next_worktime_filtered = (
            select(next_worktimes_subquery).where(next_worktimes_subquery.c.rn == 1)
        ).subquery()

        # 创建别名 - 这里需要从子查询结果中分别创建两个别名
        NextWorkTime = aliased(
            T_Tech_User_Worktime, next_worktime_filtered, name="next_worktime"
        )
        NextTimeSlot = aliased(
            T_Time_Slots, next_worktime_filtered, name="next_timeslot"
        )
        # 添加到选择列
        select_columns.extend([NextWorkTime, NextTimeSlot])

    main_query = select(*select_columns)
    if withPosition:
        main_query = main_query.outerjoin(
            LatestAddress, T_Tech_User.openid == LatestAddress.openid
        )
    if withWorktime:
        main_query = main_query.outerjoin(
            next_worktime_filtered,
            T_Tech_User.openid == next_worktime_filtered.c.tech_user_id,
        )
    main_query = main_query.where(
        T_Tech_User.work_phone != "",
        T_Tech_User.work_phone != "string",
    ).order_by(T_Tech_User.user_createtime.desc())
    if isMock == True:
        main_query = main_query.where(
            T_Tech_User.openid.like("%mock%"), T_Tech_User.openid.like("%Mock%")
        )
    elif isMock == False:
        main_query = main_query.where(
            not_(T_Tech_User.openid.like("%mock%")),
            not_(T_Tech_User.openid.like("%Mock%")),
        )
    if isOnline == True:
        main_query = main_query.where(T_Tech_User.user_online_status == "online")
    elif isOnline == False:
        main_query = main_query.where(T_Tech_User.user_online_status != "online")
    if user_nickname:
        main_query = main_query.where(
            T_Tech_User.user_nickname.like(f"%{user_nickname}%")
        )

    if city and city != "all":
        main_query = main_query.where(
            or_(
                T_Tech_User.user_city == city,
                T_Tech_User.user_city.like(f"%{city}%"),
                func.lower(city).like(f"%{func.lower(T_Tech_User.user_city)}%"),
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
    users = session.exec(main_query).all()
    count = session.exec(count_query).first()

    processed_users = []
    for user_row in users:
        if isinstance(user_row, T_Tech_User):
            user = user_row.model_dump()
            processed_users.append(user)
        else:
            user_dict = {}
            for item in user_row:
                if item:
                    if isinstance(item, T_Tech_User):
                        item = item.model_dump()
                        for key, value in item.items():
                            user_dict[key] = value
                    elif isinstance(item, TechAddress):
                        item = item.model_dump()
                        user_dict["address"] = item
                    elif isinstance(item, T_Tech_User_Worktime):
                        user_dict["work_date"] = item.work_date
                    elif isinstance(item, T_Time_Slots):
                        user_dict["work_time"] = item.start_time
            processed_users.append(user_dict)

    return {
        "totalCount": count,
        "data": processed_users,
        "currentPage": pageNumber,
        "pageSize": pageSize,
    }


# 读取技师列表
@router.get("/techlist/totalCount")
async def get_tech_list_total_count(
    session: Session = Depends(get_session),
):
    query = (
        select(T_Tech_User)
        .where(
            not_(T_Tech_User.openid.like("%mock%")),
            not_(T_Tech_User.openid.like("%Mock%")),
            T_Tech_User.work_phone != "",
            T_Tech_User.work_phone != "string",
        )
        .order_by(T_Tech_User.user_id.desc())
    )
    mock_query = (
        select(T_Tech_User)
        .where(T_Tech_User.openid.like("%mock%"), T_Tech_User.openid.like("%Mock%"))
        .order_by(T_Tech_User.user_id)
    )

    count_query = select(func.count()).select_from(query.alias())
    count_mock_query = select(func.count()).select_from(mock_query.alias())

    count = session.exec(count_query).first()
    count_mock = session.exec(count_mock_query).first()

    return {
        "techlistTotalCount": count,
        "techlistMockTotalCount": count_mock,
    }


# 读取技师个人信息
@router.get("/{openid}")
async def read_tech_user(openid: str):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
        results = session.exec(statement)
        return results.first()


# 读取技师个人信息
@router.get("/techbyUserId/{userid}")
async def read_tech_user(userid: int):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.user_id == userid)
        results = session.exec(statement)
        return results.first()


# 客户端获取单个技师信息
@router.get("/{user_id}/techWithPosition/")
async def get_tech_user(
    user_id: str,
    lon: float = None,
    lat: float = None,
    session: Session = Depends(get_session),
):
    client_lon = lon
    client_lat = lat
    base_query = (
        select(
            T_Tech_User,
            select(func.count(T_Order_Comment.order_comment_id))
            .where(T_Order_Comment.tech_id == T_Tech_User.openid)
            .scalar_subquery()
            .label("comment_count"),
            select(func.count(T_User_Follows.id))
            .where(T_User_Follows.tech_openid == T_Tech_User.openid)
            .scalar_subquery()
            .label("follow_count"),
        )
        .where(T_Tech_User.user_id == user_id)
        .options(
            selectinload(T_Tech_User.tech_user_products).selectinload(
                T_Tech_User_Product.product
            )
        )
        .options(selectinload(T_Tech_User.comments))
    )

    result = session.exec(base_query).first()
    assert result is not None, "not techuser found"
    user_result, comment_count, follow_count = result
    openid = user_result.openid
    contract_query = select(T_Tech_USER_Contract).where(
        T_Tech_USER_Contract.tech_openid == openid,
        T_Tech_USER_Contract.status == "approve",
        T_Tech_USER_Contract.dealer_name.is_not(None),
    )
    contract_result = session.exec(contract_query).first()
    dealer_name = contract_result.dealer_name if contract_result else ""
    # 查询2：获取最新位置
    position_query = (
        select(TechAddress)
        .where(TechAddress.openid == openid)
        .order_by(
            TechAddress.is_default.desc(),  # is_default=True 优先
            TechAddress.create_time.desc(),  # create_time 最近的优先
        )
    )

    latest_position = session.exec(position_query).first()  # 查询3：获取最近工作时间
    worktime_query = get_next_worktimes_query(is_subquery=False, tech_openid=openid)
    worktime_result = session.exec(worktime_query).first()
    # 计算距离
    distance = 1000
    if (
        latest_position
        and latest_position.lat is not None
        and latest_position.lon is not None
        and client_lon is not None
        and client_lat is not None
    ):
        tech_lat = latest_position.lat
        tech_lon = latest_position.lon
        distance = great_circle(
            (client_lat, client_lon), (tech_lat, tech_lon)
        ).kilometers
    worktime_date = None
    worktime_start = None
    # worktime_end = None

    if worktime_result:
        worktime_date = worktime_result[1]
        worktime_start = worktime_result[2]
        # worktime_end = timeslot_obj.end_time
    # 使用ORM关系获取关联的产品
    products = [
        tech_user_product.product
        for tech_user_product in user_result.tech_user_products
    ]

    return {
        "user_id": user_result.user_id,
        "user_phone": user_result.user_phone,
        "user_nickname": user_result.user_nickname,
        "user_sex": user_result.user_sex,
        "user_age": user_result.user_age,
        "business_license": user_result.business_license,
        "technician_certificate": user_result.technician_certificate,
        "health_certificate": user_result.health_certificate,
        # "idnetity_card": user_result.idnetity_card,
        "openid": user_result.openid,
        "headimgurl": user_result.headimgurl,
        "work_phone": user_result.work_phone,
        # "bank_card_id": user_result.bank_card_id,
        # "bank_card_type": user_result.bank_card_type,
        "user_desc": user_result.user_desc,
        "photo_work": user_result.photo_work,
        "photo_life_1": user_result.photo_life_1,
        "photo_life_2": user_result.photo_life_2,
        "photo_life_3": user_result.photo_life_3,
        "tech_user_id": latest_position.openid if latest_position else None,
        "lon": latest_position.lon if latest_position else None,
        "lat": latest_position.lat if latest_position else None,
        "address": latest_position.address if latest_position else None,
        "work_city": latest_position.city if latest_position else None,
        "refresh_time": latest_position.create_time if latest_position else None,
        "distance": distance,
        "worktime": worktime_start,
        "workdate": worktime_date,
        "comments": user_result.comments,  # 使用getattr以防comments不存在
        "comment_count": comment_count,
        "follow_count": follow_count,
        "products": products,
        "dealer_name": dealer_name,
    }


@router.get("/wechat_login/{openid}")
async def wechat_login_register(openid: str, headimgurl: str, nickname: str):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
        users = session.exec(statement)
        user = users.first()
        if user is None:
            new_user = T_Tech_User(
                openid=openid,
                headimgurl=headimgurl,
                user_nickname=nickname,
                user_age=1,
                work_phone="",
                bank_card_type="string",
                user_phone="",
                user_sex="",
                user_pwd="",
                idnetity_card="string",
                bank_card_id="string",
                user_desc="待完善",
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return {"msg": "User registered", "data": new_user}
        else:
            return {"msg": "User already registered", "data": user}


@router.post("/")
async def create_tech_user(user: T_Tech_User):
    try:
        with Session(engine) as session:
            existing_tech_user = session.exec(
                select(T_Tech_User).where(T_Tech_User.user_id == user.user_id)
            ).first()
            if existing_tech_user:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(user)
                session.commit()
                session.refresh(user)
                return {"msg": "create sucess", "data": user}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/workphoto")
async def update_tech_user_workphoto(
    openid: str,
    photo_work: UploadFile = File(None),
    session: Session = Depends(get_session),
):

    statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=400, detail="the techUser not exists.")
    # 保存上传的照片
    statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
    existing_tech = session.exec(statement).first()
    print(photo_work)
    if photo_work:
        # cdn_path = await upload_photo_to_local(photo_work, existing_tech.openid, existing_tech.user_nickname)
        cdn_path = await upload_photo_to_cdn(photo_work, openid)
        existing_tech.photo_work = cdn_path
    session.add(existing_tech)
    session.commit()
    session.refresh(existing_tech)
    return existing_tech


@router.post("/lifephoto")
async def update_tech_user_photo(
    openid: str,
    photo_life_1: UploadFile = File(None),
    photo_life_2: UploadFile = File(None),
    photo_life_3: UploadFile = File(None),
):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
        result = session.exec(statement)
        if not result.first():
            raise HTTPException(status_code=400, detail="the techUser not exists.")
        else:
            # 保存上传的照片
            statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
            existing_tech = session.exec(statement).first()
            if photo_life_1:
                cdn_path1 = await upload_photo_to_cdn(photo_life_1, openid)
                existing_tech.photo_life_1 = cdn_path1
            if photo_life_2:
                cdn_path2 = await upload_photo_to_cdn(photo_life_2, openid)
                existing_tech.photo_life_2 = cdn_path2
            if photo_life_3:
                cdn_path3 = await upload_photo_to_cdn(photo_life_3, openid)
                existing_tech.photo_life_3 = cdn_path3
            session.add(existing_tech)
            session.commit()
            session.refresh(existing_tech)
            return existing_tech


@router.put("/")
async def update_tech_user(user_id: int, newUser: T_Tech_User):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.user_id == user_id)
        result = session.exec(statement)
        user = result.one()
        user.user_pwd = newUser.user_pwd
        user.user_phone = newUser.user_phone
        user.user_nickname = newUser.user_nickname
        user.user_sex = newUser.user_sex
        user.user_age = newUser.user_age
        user.idnetity_card = newUser.idnetity_card
        user.openid = newUser.openid
        user.headimgurl = newUser.headimgurl
        user.work_phone = newUser.work_phone
        user.bank_card_id = newUser.bank_card_id
        user.bank_card_type = newUser.bank_card_type
        user.user_desc = newUser.user_desc
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"code": 200, "data": user}


@router.post("/modify/")
async def update_tech_user(
    openid: str, newUser: T_Tech_User, session: Session = Depends(get_session)
):
    statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
    result = session.exec(statement)
    user = result.one()
    user.user_nickname = newUser.user_nickname
    user.user_sex = newUser.user_sex
    user.user_age = newUser.user_age
    user.work_phone = newUser.work_phone
    user.user_city = newUser.user_city
    # 只在 newUser 中提供了值的情况下更新以下字段
    if newUser.photo_work is not None:
        user.photo_work = newUser.photo_work
    if newUser.photo_life_1 is not None:
        user.photo_life_1 = newUser.photo_life_1
    if newUser.photo_life_2 is not None:
        user.photo_life_2 = newUser.photo_life_2
    if newUser.photo_life_3 is not None:
        user.photo_life_3 = newUser.photo_life_3
    if newUser.business_license is not None:
        user.business_license = newUser.business_license
    if newUser.technician_certificate is not None:
        user.technician_certificate = newUser.technician_certificate
    if newUser.health_certificate is not None:
        user.health_certificate = newUser.health_certificate
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/modifySingle")
async def update_tech_user(openid: str, propName: str, newUser: T_Tech_User):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
        result = session.exec(statement)
        user = result.one()
        # user[propName] = newUser[propName]
        # Update the specified property
        setattr(user, propName, getattr(newUser, propName))
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


# 修改技师手机号
@router.post("/update_phone/")
async def update_tech_user_phone(user_id: str, user_phone: str):
    try:
        with Session(engine) as session:
            statement = select(T_Tech_User).where(T_Tech_User.openid == user_id)
            users = session.exec(statement)
            user = users.first()
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            # 更新 user_phone 字段
            user.user_phone = user_phone
            session.add(user)
            session.commit()
            session.refresh(user)
            # return user
            return user
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/del/{user_id}")
async def delete_tech_user(user_id: int):
    with Session(engine) as session:
        statement = select(T_Tech_User).where(T_Tech_User.user_id == user_id)
        results = session.exec(statement)
        product = results.first()
        if not product:
            return {"code": 200, "data": "there's no product"}
        session.delete(product)
        session.commit()
        return {"msg": "delete sucess", "data": product}


async def upload_photo_to_cdn(photo: UploadFile, openid: str):
    photo_filename = "Tech_User_" + openid + "_" + photo.filename
    upload_cdn_folder_path = "uploads"
    cdn_path = await upload_file_to_cdn(photo, upload_cdn_folder_path, photo_filename)
    return cdn_path


def get_main_query(
    pageNumber, pageSize, lon, lat, city, user_openid=None, name=None, product_id=None
):
    # 最新位置子查询 - 使用窗口函数找出每个技师的最新位置
    if lon and lat:
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
                ).label("approx_distance"),
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
    else:
        latest_positions_subquery = (
            select(
                TechAddress.openid,
                TechAddress.lon,
                TechAddress.lat,
                TechAddress.address,
                TechAddress.city,
                TechAddress.create_time,
                # 使用数据库函数直接计算距离(PostgreSQL)
                literal(1000).label("approx_distance"),
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

    # 下一个工作时间子查询 - 找出每个技师的下一个工作时间
    next_worktimes_subquery = get_next_worktimes_query()

    next_worktimes = (
        select(next_worktimes_subquery).where(next_worktimes_subquery.c.rn == 1)
    ).subquery()

    # 评论计数作为子查询
    comment_count_expr = (
        select(func.count(T_Order_Comment.order_comment_id))
        .where(T_Order_Comment.tech_id == T_Tech_User.openid)
        .scalar_subquery()
        .label("comment_count")
    )

    # 关注计数作为子查询
    follow_count_expr = (
        select(func.count(T_User_Follows.id))
        .where(T_User_Follows.tech_openid == T_Tech_User.openid)
        .scalar_subquery()
        .label("follow_count")
    )

    # 是否被关注检查 - 使用exists更高效
    is_followed_expr = None
    if user_openid:
        # 修正：使用case语句创建布尔表达式
        is_followed_expr = Case(
            (
                exists(
                    select(1).where(
                        and_(
                            T_User_Follows.tech_openid == T_Tech_User.openid,
                            T_User_Follows.user_openid == user_openid,
                        )
                    )
                ),
                True,
            ),
            else_=False,
        ).label("is_followed")

    # 构建主查询的列
    main_query_columns = [
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
        comment_count_expr,
        follow_count_expr,
    ]

    # 只在需要时添加is_followed列
    if user_openid:
        main_query_columns.append(is_followed_expr)

    # 主查询
    main_query = (
        select(*main_query_columns)
        .options(
            noload(T_Tech_User.orders),
            selectinload(T_Tech_User.tech_user_products).selectinload(
                T_Tech_User_Product.product
            ),
        )
        .outerjoin(latest_positions, T_Tech_User.openid == latest_positions.c.openid)
        .outerjoin(next_worktimes, T_Tech_User.openid == next_worktimes.c.tech_user_id)
        .where(T_Tech_User.user_online_status == "online")
    )

    # 城市筛选
    if city:
        main_query = main_query.where(
            or_(
                latest_positions.c.city == city,
                latest_positions.c.city.like(f"%{city}%"),
                func.lower(city).like(f"%{func.lower(latest_positions.c.city)}%"),
            )
        )
    if name:
        main_query = main_query.where(T_Tech_User.user_nickname.like(f"%{name}%"))
    if product_id:
        main_query = main_query.where(
            exists(
                select(1).where(
                    and_(
                        T_Tech_User_Product.user_id == T_Tech_User.user_id,
                        T_Tech_User_Product.product_id == product_id,
                    )
                )
            )
        )
    # 分页
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
    return main_query, count_query


def get_tech_response_from_main_query(lon, lat, results):
    response = []
    for result in results:
        user: T_Tech_User = result[0]  # T_Tech_User 对象
        position_lon = result[1]
        position_lat = result[2]
        position_address = result[3]
        position_work_city = result[4]
        position_refresh_time = result[5]
        approx_distance = result[6]
        worktime_date = result[7]
        worktime_start = result[8]
        worktime_end = result[9]
        comment_count = result[10]
        follow_count = result[11]
        is_followed = result[12] if len(result) == 13 else False

        # 使用great_circle计算精确距离
        if position_lat and position_lon and lon and lat:
            distance = great_circle((lat, lon), (position_lat, position_lon)).kilometers
        else:
            distance = 1000
        products = [
            tech_user_product.product for tech_user_product in user.tech_user_products
        ]
        # if distance > 20:
        #     worktime_date = None
        #     worktime_start = None

        user_data = {
            "user_id": user.user_id,
            "user_phone": user.user_phone,
            "user_nickname": user.user_nickname,
            "user_sex": user.user_sex,
            "user_age": user.user_age,
            # "idnetity_card": user.idnetity_card,
            "openid": user.openid,
            # "headimgurl": user.headimgurl,
            "work_phone": user.work_phone,
            # 不能返回bank信息，如需要，请创建其他接口
            # "bank_card_id": user.bank_card_id,
            # "bank_card_type": user.bank_card_type,
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
            "comment_count": comment_count,
            "follow_count": follow_count,
            "products": products,
            "is_followed": is_followed,
            "is_new_tech": True,
        }
        response.append(user_data)

    return response


# 客户查询技师列表，包含所有情况
@router.get("/techlistfromclient/")
def get_tech_users_from_client(
    lon: Union[float, int] = 0,
    lat: Union[float, int] = 0,
    city="",
    user_openid: str = None,
    pageNumber: int = 1,
    pageSize: int = 10,
    orderBy: str = "disc",
    name: str = None,
    product_id: int = None,
    session=Depends(get_session),
):
    main_query, count_query = get_main_query(
        pageNumber, pageSize, lon, lat, city, user_openid, name, product_id
    )
    if orderBy == "disc":
        if lon and lat:
            main_query = main_query.order_by(
                text(
                    """
                    CASE 
                        WHEN work_date IS NULL OR start_time IS NULL THEN 1 
                        ELSE 0 
                    END,
                    CASE WHEN work_date IS NULL THEN 1 ELSE 0 END,
                    work_date ASC,
                    CASE WHEN start_time IS NULL THEN 1 ELSE 0 END,
                    start_time ASC,
                    approx_distance
                    """
                )
            )
        else:
            main_query = main_query.order_by(
                text(
                    """
                    CASE 
                        WHEN work_date IS NULL OR start_time IS NULL THEN 1 
                        ELSE 0 
                    END,
                    CASE WHEN work_date IS NULL THEN 1 ELSE 0 END,
                    work_date ASC,
                    CASE WHEN start_time IS NULL THEN 1 ELSE 0 END,
                    start_time ASC
                    """
                )
            )
    else:
        main_query = main_query.order_by(
            text(
                """
                    CASE 
                        WHEN work_date IS NULL OR start_time IS NULL THEN 1 
                        ELSE 0 
                    END,
                    CASE WHEN work_date IS NULL THEN 1 ELSE 0 END,
                    work_date ASC,
                    CASE WHEN start_time IS NULL THEN 1 ELSE 0 END,
                    start_time ASC
                    """
            )
        )
    # 执行单次查询
    results = session.exec(main_query).all()
    response = get_tech_response_from_main_query(lon, lat, results)
    count = session.exec(count_query).first()
    response_final = {
        "totalCount": count,
        "data": response,
        "currentPage": pageNumber,
        "pageSize": pageSize,
    }
    return response_final


@router.post("/invite_her")
async def invite_her(
    params: InviteHerRequest,
    session: Session = Depends(get_session),
):
    print(params)
    client_openid = params.client_openid
    tech_openid = params.tech_openid
    # check if client has send invite for 3 times during today
    today = datetime.now().strftime("%Y-%m-%d")
    statement = select(func.count()).select_from(
        select(T_Sms_Invite).where(
            T_Sms_Invite.create_time >= today,
            T_Sms_Invite.client_openid == client_openid,
        )
    )
    count = session.exec(statement).one()
    if count >= 3:
        logger.error("今天已经发送过三条邀约信息")
        raise HTTPException(status_code=400, detail="今天已经发送过三条邀约信息")
    statement = select(T_Tech_User).where(T_Tech_User.openid == tech_openid)
    tech_user = session.exec(statement).first()
    if not tech_user:
        logger.error("tech not found")
        raise HTTPException(status_code=500, detail="tech not found")
    # 通知技师
    text = "尚阳科技提醒您，客户已向您发出上线邀请。请您方便时登录平台上线！"
    response = await send_sms(text=text, mobile=tech_user.work_phone)
    sms_invite = T_Sms_Invite(
        phone=tech_user.work_phone,
        client_openid=client_openid,
        tech_openid=tech_user.openid,
    )
    session.add(sms_invite)
    session.commit()
    return {
        "type": "tech-sms",
        "phone": tech_user.work_phone,
        "text": text,
        "data": response,
    }


def get_model_columns_with_labels(model_class):
    """获取模型的所有字段并添加标签"""
    return [
        getattr(model_class, col.name).label(col.name)
        for col in model_class.__table__.columns
    ]
