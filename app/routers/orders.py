#  订单信息

from fastapi import APIRouter, Depends
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import joinedload, noload, selectinload
from sqlmodel import Session, select
from datetime import datetime
from starlette.responses import Response

from app.core.database import engine, get_session

from app.lib.utils.benefit import calculate_benefit_for_order, maintainence_fee
from app.lib.utils.coupon import group_coupons
from app.lib.utils.order import (
    get_all_todo_orders_count_func,
    get_todo_orders_count_by_userid_func,
)
from app.model.q_OrderPayRequest import OrderPayRequest
from app.model.q_TagOrderReplaceTech import TagOrderReplaceTech
from app.model.t_coupon import T_Coupon
from app.model.t_order import T_Order
from app.model.t_order_comment import T_Order_Comment
from app.model.t_order_product import T_Order_Product
from app.model.t_order_status import T_Order_Status
from app.model.t_product import T_Product
from app.model.q_OrderCreate import OrderCreate
from app.core.config import action_status_code_dict
from app.model.t_tech_user import T_Tech_User
from app.model.t_wechat_event import T_Wechat_Events
from logger import logger


router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


def parse_service_time(service_time_str: str) -> datetime:
    # 定义可能的时间格式
    formats = [
        "%Y-%m-%d %H:%M:%S",  # 2024-12-29 15:30:00
        "%Y/%m/%d %H:%M:%S",  # 2024/12/29 15:30:00
        "%Y-%m-%d",  # 2024-12-29
        "%Y/%m/%d",  # 2024/12/29
        "%d-%m-%Y %H:%M:%S",  # 29-12-2024 15:30:00
        "%d/%m/%Y %H:%M:%S",  # 29/12/2024 15:30:00
    ]
    for fmt in formats:
        try:
            return datetime.strptime(service_time_str, fmt)
        except ValueError:
            continue
    raise ValueError("无效的时间格式")


def generate_order_number(city: str, product_name: str, service_time_str: str) -> str:
    # 解析服务时间
    service_time = parse_service_time(service_time_str)
    # 格式化服务时间
    service_time_formatted = service_time.strftime("%Y%m%d%H%M%S")
    # 生成订单号
    order_number = f"{city}{product_name}{service_time_formatted}"
    return order_number


@router.get("/")
async def read_orders(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Order)).all()
        total_count = len(total_count)
        statement = (
            select(T_Order).order_by(T_Order.order_id).offset(offset).limit(pageSize)
        )
        orders = session.exec(statement).all()
        return {
            "total_count": total_count,
            "data": orders,
            "page": pageNum,
            "page_size": pageSize,
            "total_pages": (total_count // pageSize)
            + (1 if total_count % pageSize > 0 else 0),
        }


# 查看全部订单信息
@router.get("/getOrdersFromCityManager")
async def read_orders_from_city_manager(
    pageNumber: int,
    pageSize: int,
    session=Depends(get_session),
):

    offset_value = (pageNumber - 1) * pageSize
    statement_init = (
        select(T_Order)
        .options(
            selectinload(T_Order.client),
            selectinload(T_Order.tech),
            selectinload(T_Order.order_products),
            selectinload(T_Order.order_status),
            selectinload(T_Order.order_comment),
        )
        .where(
            and_(
                T_Order.parent_order_id.is_(None),  # 加钟订单不显示在订单列表
                T_Order.service_address != "fake_address",
            )
        )
        .order_by(T_Order.order_id.desc())
    )
    count_query = select(func.count()).select_from(statement_init.alias())
    statement = statement_init.limit(pageSize).offset(offset_value)
    orders = session.exec(statement).all()
    count = session.exec(count_query).first()
    # 整合信息
    order_list = []
    open_ids = [order.client_user_id for order in orders]
    # distinct openids
    open_ids = list(set(open_ids))
    user_events_statement = select(T_Wechat_Events).where(
        T_Wechat_Events.user_openid.in_(open_ids),
        T_Wechat_Events.event_type == "scan_and_follow",
    )
    user_events = session.exec(user_events_statement).all()
    channel_dict = {}
    for event in user_events:
        channel_dict[event.user_openid] = event.scene_str
    for order in orders:
        order_info = {
            "order_id": order.order_id,
            "order_serial": order.order_serial,
            "service_time": order.service_time,
            "nickname": order.nickname,
            "payment_status": order.payment_status,
            "payment_status_code": order.payment_status_code,
            "order_status_code_client": order.order_status_code_client,
            "order_status_code_tech": order.order_status_code_tech,
            "parent_order_id": order.parent_order_id,
            "service_address": order.service_address,
            "order_cost": order.order_cost,
            "client": order.client,
            "tech": order.tech,
            "order_products": order.order_products,
            "order_status": order.order_status,
            "channel": channel_dict.get(order.client_user_id, ""),
        }
        order_list.append(order_info)

    return {
        "data": order_list,
        "totalCount": count,
        "currentPage": pageNumber,
        "pageSize": pageSize,
    }


@router.get("/order_detail_from_city_manager/{order_id}")
async def get_order_detail_from_city_manager(
    order_id: int,
    session=Depends(get_session),
):

    statement = (
        select(T_Order)
        .options(noload(T_Order.order_products), joinedload(T_Order.order_status))
        .where(T_Order.order_id == order_id)
    )
    order = session.exec(statement).first()
    compensate_coupons_statement = select(T_Coupon).where(
        T_Coupon.project == "compensate",
        T_Coupon.msg == str({"order_id": order_id}),
    )
    compensate_coupons = session.exec(compensate_coupons_statement).all()
    compensate_coupons = group_coupons(compensate_coupons)
    products = session.exec(
        select(T_Order_Product, T_Order.payment_status, T_Order.payment_status_code)
        .join(T_Order, T_Order_Product.order_id == T_Order.order_id)
        .where(
            or_(
                T_Order.order_id == order_id,
                and_(
                    T_Order.parent_order_id == order_id,
                    T_Order.payment_status_code
                    == action_status_code_dict["client"]["paid"]["code"],
                ),
            )
        )
        .options(
            noload(T_Order_Product.order),
        )
        .order_by(desc(T_Order_Product.server_time))
    ).all()
    products_all = []
    for product, payment_status, payment_status_code in products:
        product_dict = product.model_dump()
        product_dict["payment_status"] = payment_status
        product_dict["payment_status_code"] = payment_status_code
        products_all.append(product_dict)
    total_fee_paid_by_customer, tech_benefit, tax = calculate_benefit_for_order(
        order, session
    )
    order_info = {
        "order_id": order.order_id,
        "order_serial": order.order_serial,
        "create_order_time": order.create_order_time,
        "update_order_time": order.update_order_time,
        "nickname": order.nickname,
        "service_time": order.service_time,
        "payment_status": order.payment_status,
        "payment_status_code": order.payment_status_code,
        "service_address": order.service_address,
        "service_province": order.service_province,
        "service_city": order.service_city,
        "service_district": order.service_district,
        "service_street": order.service_street,
        "service_region": order.service_region,
        "service_detail_address": order.service_detail_address,
        "travel_distance": order.travel_distance,
        "travel_cost": order.travel_cost,
        "order_cost": order.order_cost,
        "remark": order.remark,
        "client": order.client,
        "create_order_time": order.create_order_time,
        "tech": order.tech,
        "actual_tech": order.actual_tech,
        "coupon_value": order.coupon_value,
        "order_products": products_all,
        "order_status": order.order_status,
        "order_comment": order.order_comment,
        "order_status_code_client": order.order_status_code_client,
        "order_status_code_tech": order.order_status_code_tech,
        "total_fee_paid_by_customer": total_fee_paid_by_customer,
        "tax": tax,
        "tech_benefit": tech_benefit,
        "maintenance_fee": maintainence_fee,
        "compensate_coupons": compensate_coupons,
    }

    return order_info


# 查看订单详情
@router.get("/tech_order_detail/{order_id}")
async def read_order(order_id: str):
    with Session(engine) as session:
        statement = (
            select(T_Order)
            .options(noload(T_Order.order_products), joinedload(T_Order.order_status))
            .where(T_Order.order_id == order_id)
        )
        order = session.exec(statement).first()
        products = session.exec(
            select(T_Order_Product, T_Order.payment_status, T_Order.payment_status_code)
            .join(T_Order, T_Order_Product.order_id == T_Order.order_id)
            .where(
                or_(
                    T_Order.order_id == order_id,
                    and_(
                        T_Order.parent_order_id == order_id,
                        T_Order.payment_status_code
                        == action_status_code_dict["client"]["paid"]["code"],
                    ),
                )
            )
            .options(
                noload(T_Order_Product.order),
            )
            .order_by(desc(T_Order_Product.server_time))
        ).all()
        products_all = []
        for product, payment_status, payment_status_code in products:
            product_dict = product.model_dump()
            product_dict["payment_status"] = payment_status
            product_dict["payment_status_code"] = payment_status_code
            products_all.append(product_dict)
        total_fee_paid_by_customer, tech_benefit, tax = calculate_benefit_for_order(
            order, session
        )
        order_info = {
            "total_fee_paid_by_customer": total_fee_paid_by_customer,
            "tech_benefit": tech_benefit,
            "tax": tax,
            "order_id": order.order_id,
            "order_serial": order.order_serial,
            "create_order_time": order.create_order_time,
            "update_order_time": order.update_order_time,
            "nickname": order.nickname,
            "service_time": order.service_time,
            "payment_status": order.payment_status,
            "payment_status_code": order.payment_status_code,
            "service_address": order.service_address,
            "service_province": order.service_province,
            "service_city": order.service_city,
            "service_district": order.service_district,
            "service_street": order.service_street,
            "service_region": order.service_region,
            "service_detail_address": order.service_detail_address,
            "travel_distance": order.travel_distance,
            "travel_cost": order.travel_cost,
            "order_cost": order.order_cost,
            "remark": order.remark,
            "client": order.client,
            "create_order_time": order.create_order_time,
            "tech": order.tech,
            "coupon_value": order.coupon_value,
            "order_products": products_all,
            "order_status": order.order_status,
            "order_comment": order.order_comment,
            "order_status_code_client": order.order_status_code_client,
            "order_status_code_tech": order.order_status_code_tech,
        }
        return order_info


# 技师查看自己的订单
@router.get("/techOrderList/{user_id}")
async def read_orders_from_tech(
    user_id: str, pageNumber: int, pageSize: int, session=Depends(get_session)
):
    offset_value = (pageNumber - 1) * pageSize
    statement_init = (
        select(T_Order)
        .options(
            # 一对一，多对一用joinedload , 一对多/多对多用selectinload
            # joinedload只执行一次查询，selectinload会多一次查询（每一个selectinload查询一次）
            # selectinload,虽然查询次数更多,但效率更高
            selectinload(T_Order.client),
            selectinload(T_Order.tech),
            selectinload(T_Order.order_products),
            selectinload(T_Order.order_status),
            selectinload(T_Order.order_comment),
        )
        .where(
            and_(
                T_Order.tech_user_id == user_id,
                T_Order.parent_order_id.is_(None),  # 加钟订单不显示在订单列表
            )
        )
        .order_by(T_Order.order_id.desc())
    )
    count_query = select(func.count()).select_from(statement_init.alias())
    statement = statement_init.limit(pageSize).offset(offset_value)
    orders = session.exec(statement).all()
    count = session.exec(count_query).first()
    # 整合信息
    order_list = []
    for order in orders:
        order_info = {
            "order_id": order.order_id,
            "order_serial": order.order_serial,
            "service_time": order.service_time,
            "service_address": order.service_address,
            "order_cost": order.order_cost,
            "nickname": order.nickname,
            "travel_mode": order.travel_mode,
            "travel_cost": order.travel_cost,
            "payment_status": order.payment_status,
            "payment_status_code": order.payment_status_code,
            "order_status_code_client": order.order_status_code_client,
            "order_status_code_tech": order.order_status_code_tech,
            "order_products": order.order_products,
            "order_status": order.order_status,
            "client": order.client,
            "tech": order.tech,
        }
        order_list.append(order_info)
    return {
        "data": order_list,
        "totalCount": count,
        "currentPage": pageNumber,
        "pageSize": pageSize,
    }


# 技师进行中的订单数，放在技师端底部订单的badge
@router.get("/techOrderList/toDoOrdersCount/{user_id}")
async def get_todo_orders_count_by_userid(user_id: str, session=Depends(get_session)):
    order_count = get_todo_orders_count_by_userid_func(user_id, session)
    return order_count


# 管理后台进行中的订单数，底部订单的badge， 判断已经支付未结束的订单
@router.get("/allToDoOrdersCount")
async def get_todo_orders_count(session=Depends(get_session)):
    order_count = get_all_todo_orders_count_func(session)
    return order_count


# 客户查看自己的订单
@router.get("/clientOrderList/client/{user_id}")
async def read_orders_from_client(
    user_id: str,
    pageNumber: int,
    pageSize: int,
    session=Depends(get_session),
):

    offset_value = (pageNumber - 1) * pageSize
    statement_init = (
        select(T_Order)
        .options(
            selectinload(T_Order.client),
            selectinload(T_Order.tech),
            selectinload(T_Order.order_products),
            selectinload(T_Order.order_status),
            selectinload(T_Order.order_comment),
        )
        .where(
            and_(
                T_Order.client_user_id == user_id,
                T_Order.parent_order_id.is_(None),  # 加钟订单不显示在订单列表
            )
        )
        .order_by(T_Order.order_id.desc())
    )
    count_query = select(func.count()).select_from(statement_init.alias())
    statement = statement_init.limit(pageSize).offset(offset_value)
    orders = session.exec(statement).all()
    count = session.exec(count_query).first()
    # 整合信息
    order_list = []
    for order in orders:
        order_info = {
            "order_id": order.order_id,
            "order_serial": order.order_serial,
            "create_order_time": order.create_order_time,
            "update_order_time": order.update_order_time,
            "service_time": order.service_time,
            "payment_status": order.payment_status,
            "payment_status_code": order.payment_status_code,
            "service_address": order.service_address,
            "service_province": order.service_province,
            "service_city": order.service_city,
            "service_district": order.service_district,
            "service_street": order.service_street,
            "service_region": order.service_region,
            "service_detail_address": order.service_detail_address,
            "travel_distance": order.travel_distance,
            "travel_cost": order.travel_cost,
            "coupon_value": order.coupon_value,
            "order_cost": order.order_cost,
            "remark": order.remark,
            "client": order.client,
            "tech": order.tech,
            "order_status_code_client": order.order_status_code_client,
            "order_status_code_tech": order.order_status_code_tech,
            "order_products": order.order_products,
            "order_status": order.order_status,
            "order_comment": order.order_comment,
        }
        order_list.append(order_info)

    return {
        "data": order_list,
        "totalCount": count,
        "currentPage": pageNumber,
        "pageSize": pageSize,
    }


@router.get("/{order_id}")
async def read_order(order_id: str):
    with Session(engine) as session:
        statement = select(T_Order).where(T_Order.order_id == order_id)
        results = session.exec(statement)
        return results.first()


# 查看订单详情
@router.get("/clientOrderList/{order_id}")
async def read_order(order_id: str):
    with Session(engine) as session:
        statement = (
            select(T_Order)
            .options(noload(T_Order.order_products), joinedload(T_Order.order_status))
            .where(T_Order.order_id == order_id)
        )
        order = session.exec(statement).first()
        products = session.exec(
            select(T_Order_Product, T_Order.payment_status, T_Order.payment_status_code)
            .join(T_Order, T_Order_Product.order_id == T_Order.order_id)
            .where(
                or_(
                    T_Order.order_id == order_id,
                    and_(
                        T_Order.parent_order_id == order_id,
                        T_Order.payment_status_code
                        == action_status_code_dict["client"]["paid"]["code"],
                    ),
                )
            )
            .options(
                noload(T_Order_Product.order),
            )
            .order_by(desc(T_Order_Product.server_time))
        ).all()
        products_all = []
        for product, payment_status, payment_status_code in products:
            product_dict = product.model_dump()
            product_dict["payment_status"] = payment_status
            product_dict["payment_status_code"] = payment_status_code
            products_all.append(product_dict)
        order_info = {
            "order_id": order.order_id,
            "order_serial": order.order_serial,
            "create_order_time": order.create_order_time,
            "update_order_time": order.update_order_time,
            "nickname": order.nickname,
            "service_time": order.service_time,
            "payment_status": order.payment_status,
            "payment_status_code": order.payment_status_code,
            "service_address": order.service_address,
            "service_province": order.service_province,
            "service_city": order.service_city,
            "service_district": order.service_district,
            "service_street": order.service_street,
            "service_region": order.service_region,
            "service_detail_address": order.service_detail_address,
            "travel_distance": order.travel_distance,
            "travel_cost": order.travel_cost,
            "order_cost": order.order_cost,
            "remark": order.remark,
            "client": order.client,
            "create_order_time": order.create_order_time,
            "tech": order.tech,
            "coupon_value": order.coupon_value,
            "order_products": products_all,
            "order_status": order.order_status,
            "order_comment": order.order_comment,
            "order_status_code_client": order.order_status_code_client,
            "order_status_code_tech": order.order_status_code_tech,
        }
        return order_info


@router.post("/tag_replace_tech")
def tag_replace_tech(
    request: TagOrderReplaceTech, session: Session = Depends(get_session)
):
    order_id = request.order_id
    actual_tech_openid = request.actual_tech_openid
    statement = select(T_Order).where(T_Order.order_id == order_id)
    order = session.exec(statement).first()
    order.actual_tech_openid = actual_tech_openid
    session.commit()
    actual_tech: T_Tech_User = order.actual_tech
    actual_tech = actual_tech.model_dump()
    return actual_tech


@router.post("/del/{order_id}")
async def delete_order(order_id: int):
    with Session(engine) as session:
        statement = select(T_Order).where(T_Order.order_id == order_id)
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}
