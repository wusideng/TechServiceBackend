#  订单信息
from datetime import datetime, timedelta
import os

import httpx
import xmltodict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response

from sqlmodel import Session, select


from app.lib.utils.benefit import calculate_benefit_for_order
from app.lib.utils.upload import upload_file_to_cdn
from app.model.t_bill import T_Bill
from app.model.t_order import T_Order
from app.core.config import action_status_code_dict
from app.core.database import engine, get_session
from app.model.t_order_product import T_Order_Product
from app.model.t_order_status import T_Order_Status
from app.model.t_tech_busy_time import T_Tech_Busy_Time
from app.routers.order_pay import delete_tech_busy_time
from logger import logger


router = APIRouter(
    prefix="/ordersStatus",
    tags=["ordersStatus"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_orders(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Order_Status)).all()
        total_count = len(total_count)
        statement = (
            select(T_Order_Status)
            .order_by(T_Order_Status.order_status_id)
            .offset(offset)
            .limit(pageSize)
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


@router.get("/{order_status_id}")
async def read_orderstatus_by_id(order_status_id: str):
    with Session(engine) as session:
        statement = select(T_Order_Status).where(
            T_Order_Status.order_status_id == order_status_id
        )
        results = session.exec(statement)
        return results.first()


@router.get("/orderstatus/{order_id}")
async def read_orderstatus_by_orderid(order_id: str):
    with Session(engine) as session:
        statement = (
            select(T_Order_Status)
            .where(T_Order_Status.order_id == order_id)
            .order_by(T_Order_Status.order_status_type_code)
        )
        results = session.exec(statement).all()
        return results


# 创建订单，结束订单
@router.post("/")
async def create_order_status(
    order_status: T_Order_Status, session: Session = Depends(get_session)
):
    try:
        existing_order_status = session.exec(
            select(T_Order_Status).where(
                T_Order_Status.order_status_id == order_status.order_status_id
            )
        ).first()
        if existing_order_status:
            raise HTTPException(
                status_code=400,
                detail="Item with this unique field already exists.",
            )
        session.add(order_status)
        order = session.exec(
            select(T_Order).where(T_Order.order_id == order_status.order_id)
        ).first()
        if order is None:
            raise HTTPException(status_code=401, detail="order not exist.")
        status_type_code = order_status.order_status_type_code
        if order_status.order_operator == "client":
            # 在 SQLModel/SQLAlchemy 中，当你修改了查询出来的对象的属性后，在执行 session.commit() 时，这些修改会自动同步到数据库中
            order.order_status_code_client = status_type_code
        else:
            order.order_status_code_tech = status_type_code
        change_tech_busy_time(order, status_type_code, session)
        if status_type_code == action_status_code_dict["tech"]["service_end"]["code"]:
            [total_fee_paid_by_customer, tech_benefit] = calculate_benefit_for_order(
                order, session
            )
            bill = T_Bill(
                amount=total_fee_paid_by_customer,
                order_id=order.order_id,
                tech_income=tech_benefit,
                travel_cost=order.travel_cost,
                openid=order.tech.openid,
                user_nickname=order.tech.user_nickname,
                ratio=order.tech.ratio,
                work_city=order.service_city,
                withdrawed=False,
            )
            session.add(bill)

        session.commit()
        session.refresh(order_status)
        return {"msg": "create sucess", "data": order_status}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=401, detail="other error.")


# 报备订单状态
@router.post("/status")
async def create_order_status(order_status: T_Order_Status):
    try:
        with Session(engine) as session:
            session.add(order_status)
    except Exception as e:
        logger.exception()(e)
        session.rollback()
        raise HTTPException(status_code=401, detail="other error.")


# 上报订单状态，并添加照片报备
@router.post("/update_from_tech")
# file: (binary)
# order_id: 1
# order_status_type_code: order_022
# order_status_type: 已经出发
async def update_order_status_from_tech(
    order_id: str,
    order_operator: str,
    order_status_type_code: str,
    order_status_type: str,
    file: UploadFile = File(None),
):
    try:
        if not file.filename.endswith((".png", ".jpg", ".jpeg")):
            raise HTTPException(status_code=401, detail="Invalid file format.")
        photo_filename = "Order_" + order_id + order_status_type + "_" + file.filename
        upload_cdn_folder_path = "uploads"
        cdn_path = await upload_file_to_cdn(
            file, upload_cdn_folder_path, photo_filename
        )
        order_status = T_Order_Status(
            order_id=int(order_id),
            order_status_type_code=order_status_type_code,
            order_status_type=order_status_type,
            order_status_photo=cdn_path,
            order_operator=order_operator,
        )
        with Session(engine) as session:
            statement = select(T_Order).where(T_Order.order_id == order_id)
            order = session.exec(statement).first()
            order.order_status_code_tech = order_status_type_code
            session.add(order_status)
            change_tech_busy_time(order, order_status_type_code, session)
            session.commit()
            session.refresh(order)
            return order
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=401, detail="other error.")


# async def create_order(order_status: T_Order_Status, file: UploadFile = File(None)):
#     try:
#         with Session(engine) as session:
#             existing_order = session.exec(select(T_Order_Status).where(T_Order_Status.order_status_id == order_status.order_status_id)).first()
#             if existing_order:
#                 raise HTTPException(status_code=400, detail="Item with this unique field already exists.")
#             else:
#                 session.add(order_status)
#                 session.commit()
#                 session.refresh(order_status)
#                 return {"msg":"create sucess", "data": order_status}
#     except IntegrityError:
#         raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_order(order_status_id: int, newOrderProd: T_Order_Status):
    with Session(engine) as session:
        statement = select(T_Order_Status).where(
            T_Order_Status.order_status_id == order_status_id
        )
        result = session.exec(statement)
        order = result.one()
        order.order_id = newOrderProd.order_id
        order.order_status_type_code = newOrderProd.order_status_type_code
        order.order_status_type = newOrderProd.order_status_type
        order.order_status_time = newOrderProd.order_status_time
        session.add(order)
        session.commit()
        session.refresh(order)
        return order


@router.post("/del/{order_status_id}")
async def delete_order(order_status_id: int):
    with Session(engine) as session:
        statement = select(T_Order_Status).where(
            T_Order_Status.order_status_id == order_status_id
        )
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}


def change_tech_busy_time(
    order: T_Order, order_status_type_code: str, session: Session
):
    if (
        order_status_type_code == action_status_code_dict["tech"]["has_left"]["code"]
        or order_status_type_code
        == action_status_code_dict["client"]["service_end"]["code"]
    ):
        delete_tech_busy_time(order.order_id, session)
    if (
        order_status_type_code
        == action_status_code_dict["tech"]["start_service"]["code"]
        and order.parent_order_id is None
    ):
        tech_busytime_statment = select(T_Tech_Busy_Time).where(
            T_Tech_Busy_Time.order_id == order.order_id
        )
        order_product: T_Order_Product = order.order_products[0]
        duration: int = int(order_product.duration.split("分钟")[0])
        tech_busytime = session.exec(tech_busytime_statment).first()
        product_count = order_product.product_count
        new_end_time = datetime.now() + timedelta(minutes=product_count * duration)
        if tech_busytime:
            tech_busytime.end_time = new_end_time
        else:
            tech_busytime = T_Tech_Busy_Time(
                tech_user_openid=order.tech_user_id,
                order_id=order.order_id,
                start_time=datetime.now(),
                end_time=new_end_time,
            )
