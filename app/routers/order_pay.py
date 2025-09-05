import asyncio
import httpx
from starlette.responses import Response
import xmltodict
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.core.config import settings
from config import pay_test_openids
from app.core.database import engine
from app.core.util import (
    generate_nonce_str,
    generate_signature,
    retry_request,
    default_travel_time_for_slot_calculation_minutes,
)
from app.lib.utils.order_pay import (
    generate_order_data,
    generate_response_from_wx_pay_response,
    get_existing_order_and_latest_product,
)
from app.lib.utils.sql_query import delete_tech_busy_time
from app.model.q_OrderExtendService import OrderExtendServiceRequest
from app.model.q_OrderPayRequest import ContinueToPayRequest, OrderPayRequest
from app.model.q_OrderPaymentUpdate import OrderPaymentUpdateRequest
from app.model.t_coupon import T_Coupon
from app.model.t_order import T_Order
from app.model.t_order_product import T_Order_Product
from app.model.t_order_status import T_Order_Status
from app.model.t_product import T_Product
from app.model.q_OrderCreate import OrderCreate
from app.core.config import action_status_code_dict
from app.model.t_tech_busy_time import T_Tech_Busy_Time
from app.model.t_tech_user import T_Tech_User
from app.model.wx_pay.v2.payment_notify_request import (
    PaymentNotifyRequestOnReturnCodeSuccess,
)
from app.routers.orders import generate_order_number
from app.routers.voice_sms_hywx import send_voice_order
from app.routers.virtual_tel_yxlk import bind_phone_by_order
from config import order_pay_timeout

from logger import logger

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.post("/extendService")
async def create_extendService_wxpay(
    request: OrderExtendServiceRequest,
    background_tasks: BackgroundTasks,  # 注入BackgroundTasks
):
    try:
        user_openid = request.user_openid
        product_count = request.product_count
        assert product_count > 0
        order_id = request.order_id
        with Session(engine) as session:
            existing_order, latest_product = get_existing_order_and_latest_product(
                order_id=order_id, session=session, user_openid=request.user_openid
            )
            product = session.exec(
                select(T_Product).where(T_Product.product_id == request.product_id)
            ).first()
            assert product is not None, "product not found"
            assert (
                existing_order.payment_status_code
                == action_status_code_dict["client"]["paid"]["code"]
            ), "parent order not paid"
            assert (
                existing_order.order_status_code_client
                != action_status_code_dict["client"]["service_end"]["code"]
            ), "parent order already ended"
            assert (
                existing_order.order_status_code_tech
                == action_status_code_dict["tech"]["start_service"]["code"]
                or existing_order.order_status_code_tech
                == action_status_code_dict["tech"]["has_arrived"]["code"]
            ), "parent order not started"
            assert existing_order.client_user_id == user_openid, "user not match"
        order_cost = product.price_current * product_count
        order_data = generate_order_data(
            product_name=product.product_name,
            order_cost=order_cost,
            user_openid=user_openid,
        )
        result = await request_to_pay_towx(order_data)
        order_id = create_extend_service_order(
            existing_order=existing_order,
            latest_product=latest_product,
            product=product,
            out_trade_no=order_data["out_trade_no"],
            product_count=product_count,
            order_cost=order_cost,
        )
        background_tasks.add_task(check_order_timeout, order_id)
        return generate_response_from_wx_pay_response(
            result=result,
            order_id=order_id,
            order_data=order_data,
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/createwxpay/")
async def create_order_wxpay(
    orderPayRequest: OrderPayRequest,
    background_tasks: BackgroundTasks,  # 注入BackgroundTasks
):
    try:
        product_id = orderPayRequest.order_product_info.product.product_id
        with Session(engine) as session:
            product_price = session.exec(
                select(T_Product.price_current).where(
                    T_Product.product_id == product_id
                )
            ).first()
            assert product_price is not None
        order_cost = (
            product_price * orderPayRequest.order_product_info.product.product_count
            + orderPayRequest.order_product_info.order.travel_cost * 2
            - orderPayRequest.order_product_info.order.coupon_value
        )
        # 测试数据 Begin
        logger.info(f"pay_test_openids: {pay_test_openids}")
        order_cost = 1 if orderPayRequest.clientOpenId in pay_test_openids else 0  # 判断并赋值
        # 测试数据 End
        order_data = generate_order_data(
            product_name=orderPayRequest.prodname,
            order_cost=order_cost,
            user_openid=orderPayRequest.clientOpenId,
        )
        # 发送请求到微信支付
        result = await request_to_pay_towx(order_data)
        order_id = create_new_order(
            orderPayRequest.order_product_info.order,
            orderPayRequest.order_product_info.product,
            order_data["out_trade_no"],
        )
        background_tasks.add_task(check_order_timeout, order_id)
        return generate_response_from_wx_pay_response(
            result=result,
            order_id=order_id,
            order_data=order_data,
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))


# 这里可能是因为不是请求，直接变成了字典
def create_new_order(
    order: T_Order, product: T_Order_Product, out_trade_no: str
) -> T_Order:
    try:
        with Session(engine) as session:
            existing_order = session.exec(
                select(T_Order).where(T_Order.order_id == order.order_id)
            ).first()
            if existing_order:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            existing_product = session.exec(
                select(T_Product).where(T_Product.product_id == product.product_id)
            ).first()
            if existing_product is None:
                raise HTTPException(
                    status_code=401, detail="Item with this unique field not exists."
                )

            order.order_serial = generate_order_number(
                order.service_city, "上门按摩", order.service_time
            )
            order.out_trade_no = out_trade_no
            # 创建订单时为待支付
            order.payment_status = action_status_code_dict["client"][
                "wait_for_payment"
            ]["text"]
            order.payment_status_code = action_status_code_dict["client"][
                "wait_for_payment"
            ]["code"]
            session.add(order)
            session.commit()

            new_order_status = T_Order_Status(
                order_id=order.order_id,
                order_status_type_code=action_status_code_dict.get("client")
                .get("wait_for_payment")
                .get("code"),
                order_status_type=action_status_code_dict.get("client")
                .get("wait_for_payment")
                .get("text"),
                order_operator="client",
            )
            product.order_id = order.order_id  # 设置订单 ID
            product.product_name = existing_product.product_name
            # 保存到order status表
            session.add(new_order_status)
            # 保存到order product表
            session.add(product)
            logger.info(f"保存订单状态成功,{new_order_status}")
            logger.info(f"保存产品成功,{product}")
            session.commit()
            session.refresh(order)
            logger.info("保存订单成功:{order}")
            return order.order_id
            # 完成订单入库

            # 进行微信支付流程（支付成功，取消支付，支付失败）
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=410, detail="other error.")


# only used for update client payment
@router.post("/payment_update/")
async def order_payment_update(order: OrderPaymentUpdateRequest):
    logger.info("order payment update")
    try:
        with Session(engine) as session:
            existing_order = session.exec(
                select(T_Order).where(T_Order.order_id == order.order_id)
            ).first()
            assert existing_order is not None, "order not found"
            logger.info(f"支付状态:{order.payment_status}")
            if (
                order.payment_status_code
                == action_status_code_dict["client"]["paid"]["code"]
            ):
                # 用户使用了优惠券，那么标记优惠券为已经使用
                if order.coupon_id:
                    existing_order.coupon_id = order.coupon_id
                    coupon = session.exec(
                        select(T_Coupon).where(T_Coupon.coupon_id == order.coupon_id)
                    ).first()
                    # 验证优惠券是否属于该用户
                    assert (
                        coupon.open_id == existing_order.client_user_id
                    ), "coupon not belong to this user"
                    coupon.coupon_status = "used"
                # 已支付则发送订单通知信息
                logger.info(f"通知:{order.order_id}")
                asyncio.create_task(send_voice_order(order.order_id))
                asyncio.create_task(bind_phone_by_order(order.order_id))
                set_tech_busy_time(session, existing_order)

            if (
                existing_order.actual_fee_received
                and existing_order.actual_fee_received > 0
            ):
                # 存在异步通知消息先到达的可能性
                session.commit()
                return existing_order
            existing_order.payment_status = order.payment_status
            existing_order.payment_status_code = order.payment_status_code
            # existing_order.order_status_code_client = order.order_status_code_client
            new_order_status = T_Order_Status(
                order_id=order.order_id,
                order_status_type_code=order.payment_status_code,
                order_status_type=order.payment_status,
                order_operator="client",
            )
            # todo verify the actual fee recieved is greater than the fee in the order
            session.add(new_order_status)
            session.commit()
            session.refresh(existing_order)
            logger.info(f"保存订单成功_update_payment:{existing_order}")
            return existing_order
            # 完成订单入库

            # 进行微信支付流程（支付成功，取消支付，支付失败）
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=410, detail="other error.")


@router.post("/wxpay_notify")
async def wx_pay_notify(request: Request):
    # todo 对通知做签名认证，并校验返回的订单金额是否与商户侧的订单金额一致，防止数据泄露导致出现“假通知”，造成资金损失
    logger.info("received payment notify, wxpay_notify")
    notify_data = await request.body()
    notify_info = xmltodict.parse(notify_data.decode("utf-8"))
    logger.info(f"notify_info:{notify_info}")
    if notify_info["xml"]["return_code"] == "SUCCESS":
        notify_info: PaymentNotifyRequestOnReturnCodeSuccess = (
            PaymentNotifyRequestOnReturnCodeSuccess(**notify_info["xml"])
        )
        out_trade_no = notify_info.out_trade_no
        with Session(engine) as session:
            statement = select(T_Order).where(T_Order.out_trade_no == out_trade_no)
            existing_order = session.exec(statement).first()
            if (
                existing_order.actual_fee_received
                and existing_order.actual_fee_received > 0
            ):
                logger.info("this is possibly a duplicate notification of payment")
                xml_content = xmltodict.unparse(
                    {"xml": {"return_code": "SUCCESS", "return_msg": "ok"}}
                )
                return Response(content=xml_content, media_type="text/xml")
            # result_code 只有SUCCESS/FAIL
            status = notify_info.result_code
            logger.info(
                f"payment notification get successfully, out_trade_no:{out_trade_no},status: {status}"
            )
            if status == "SUCCESS":
                payment_status = action_status_code_dict["client"]["paid"]["text"]
                payment_status_code = action_status_code_dict["client"]["paid"]["code"]
                existing_order.actual_fee_received = (
                    notify_info.cash_fee
                    if notify_info.cash_fee
                    else notify_info.total_fee
                )
            else:
                logger.info(
                    "payment failed,out_trade_no:{out_trade_no},status: {status}"
                )
                payment_status = action_status_code_dict["client"]["payment_failed"][
                    "text"
                ]
                payment_status_code = action_status_code_dict["client"][
                    "payment_failed"
                ]["code"]
            existing_order.payment_status = payment_status
            existing_order.payment_status_code = payment_status_code
            # 多次commit,预防死锁发生
            session.commit()
            new_order_status = T_Order_Status(
                order_id=existing_order.order_id,
                order_status_type_code=payment_status_code,
                order_status_type=payment_status,
                order_operator="wxpay",
            )
            session.add(new_order_status)
            session.commit()
    logger.info("return response of payment")
    xml_content = xmltodict.unparse(
        {"xml": {"return_code": "SUCCESS", "return_msg": "ok"}}
    )
    return Response(content=xml_content, media_type="text/xml")


@router.post("/continuetopay/")
async def continue_to_pay(
    order_info: ContinueToPayRequest,
    background_tasks: BackgroundTasks,  # 注入BackgroundTasks
):
    with Session(engine) as session:
        existing_order, latest_product = get_existing_order_and_latest_product(
            order_id=order_info.order_id,
            session=session,
            user_openid=order_info.user_id,
        )
        assert existing_order is not None, "order not found"
        assert existing_order.out_trade_no is not None, "out_trade_no not found"
        assert (
            existing_order.payment_status_code
            == action_status_code_dict["client"]["payment_failed"]["code"]
        ), "order not in payment failed status"

        assert existing_order is not None, "order not found"
        assert existing_order.out_trade_no is not None, "out_trade_no not found"
        assert (
            existing_order.payment_status_code
            == action_status_code_dict["client"]["payment_failed"]["code"]
        ), "order not in payment failed status"
        time_difference = datetime.now() - existing_order.create_order_time
        if time_difference > timedelta(seconds=order_pay_timeout):
            existing_order.payment_status = action_status_code_dict["client"][
                "payment_timeout"
            ]["text"]
            existing_order.payment_status_code = action_status_code_dict["client"][
                "payment_timeout"
            ]["code"]
            session.commit()
            return {"error": "支付超时"}
        # 满足支付条件，先把之前的单子给关了
        await close_wx_order(out_trade_no=existing_order.out_trade_no)
        # 好像这里不用改状态也行，改了反倒不方便，previous_pay_closed没啥用，先不用了
        # existing_order.payment_status = action_status_code_dict["client"][
        #     "previous_pay_closed"
        # ]["text"]
        # existing_order.payment_status_code = action_status_code_dict["client"][
        #     "previous_pay_closed"
        # ]["code"]
        # session.commit()
        # 重新生成订单
        order_cost = existing_order.order_cost
        order_data = generate_order_data(
            product_name=latest_product.product_name,
            order_cost=order_cost,
            user_openid=existing_order.client_user_id,
        )

        result = await request_to_pay_towx(order_data)
        # 将订单重新标记为待支付
        existing_order.out_trade_no = order_data["out_trade_no"]
        existing_order.create_order_time = datetime.now()
        existing_order.payment_status = action_status_code_dict["client"][
            "wait_for_payment"
        ]["text"]
        existing_order.payment_status_code = action_status_code_dict["client"][
            "wait_for_payment"
        ]["code"]
        new_order_status = T_Order_Status(
            order_id=existing_order.order_id,
            order_status_type_code=action_status_code_dict.get("client")
            .get("wait_for_payment")
            .get("code"),
            order_status_type=action_status_code_dict.get("client")
            .get("wait_for_payment")
            .get("text"),
            order_operator="client",
        )
        session.add(new_order_status)
        session.commit()
        background_tasks.add_task(check_order_timeout, existing_order.order_id)
        return generate_response_from_wx_pay_response(
            result=result,
            order_id=existing_order.order_id,
            order_data=order_data,
        )


@retry_request(retry_times=3, interval=3)
async def close_wx_order(out_trade_no: str):
    order_data = {
        "appid": settings.APPID,
        "mch_id": settings.MCHID,
        "out_trade_no": out_trade_no,
        "nonce_str": generate_nonce_str(),
    }
    order_data["sign"] = generate_signature(order_data)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.mch.weixin.qq.com/pay/closeorder",
            data=xmltodict.unparse({"xml": order_data}),
            headers={"Content-Type": "text/xml"},
        )
    result = xmltodict.parse(response.content)
    assert result["xml"]["return_code"] == "SUCCESS", "close order failed"
    assert result["xml"]["result_code"] == "SUCCESS", "close order failed"
    return result


@retry_request(retry_times=3, interval=3)
async def request_to_pay_towx(order_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.mch.weixin.qq.com/pay/unifiedorder",
            data=xmltodict.unparse({"xml": order_data}),
            headers={"Content-Type": "text/xml"},
        )
    result = xmltodict.parse(response.content)
    if result["xml"]["return_code"] == "SUCCESS":
        return result
    else:
        logger.info(result["xml"])
        raise HTTPException(status_code=400, detail=str(e))
    # 这个请求返回后会弹出微信付钱的弹框，在这里就先把订单生成放入order表里
    # 因为order_product_info内部嵌套过多，被系统解析成了字典


async def check_order_timeout(order_id: int):
    logger.info("check order timeout:")
    # 等待超时时间,超时时间为秒
    await asyncio.sleep(order_pay_timeout)

    # 使用 with 语句创建会话
    with Session(engine) as session:
        # 查询订单状态
        statement = select(T_Order).where(T_Order.order_id == order_id)
        existing_order = session.exec(statement).first()

        if existing_order and (
            existing_order.payment_status_code
            == action_status_code_dict["client"]["wait_for_payment"]["code"]
            or existing_order.payment_status_code
            == action_status_code_dict["client"]["payment_failed"]["code"]
        ):
            # 更新为超时状态
            existing_order.payment_status_code = action_status_code_dict["client"][
                "payment_timeout"
            ]["code"]
            existing_order.payment_status = action_status_code_dict["client"][
                "payment_timeout"
            ]["text"]
            logger.info(f"update order to timeout, order_id:{existing_order.order_id}")
            session.commit()
            # logger.info(f"订单 {order_id} 已超时")


def create_extend_service_order(
    existing_order: T_Order,
    latest_product: T_Order_Product,
    product: T_Product,
    out_trade_no: str,
    product_count: int,
    order_cost: int,
) -> int:
    current_time = datetime.now()
    service_end_time = latest_product.server_time + timedelta(
        minutes=int(latest_product.duration.replace("分钟", ""))
        * latest_product.product_count
    )
    if current_time > service_end_time:
        next_service_time = current_time
    else:
        next_service_time = service_end_time
    with Session(engine) as session:
        new_order = T_Order(
            service_time=next_service_time,
            service_address=existing_order.service_address,
            service_province=existing_order.service_province,
            service_city=existing_order.service_city,
            service_district=existing_order.service_district,
            service_street=existing_order.service_street,
            service_region=existing_order.service_region,
            service_detail_address=existing_order.service_detail_address,
            travel_distance=0,
            travel_cost=0,
            travel_time=0,
            nickname=existing_order.nickname,
            payment_mode=existing_order.payment_mode,
            payment_status=action_status_code_dict["client"]["wait_for_payment"][
                "text"
            ],
            payment_status_code=action_status_code_dict["client"]["wait_for_payment"][
                "code"
            ],
            tech_user_id=existing_order.tech_user_id,
            client_user_id=existing_order.client_user_id,
            order_cost=order_cost,
            out_trade_no=out_trade_no,
            remark=existing_order.remark,
            coupon_value=0,
            parent_order_id=existing_order.order_id,
        )
        session.add(new_order)
        session.commit()
        logger.info(f"保存加钟订单成功,{new_order}")
        new_order_status = T_Order_Status(
            order_id=new_order.order_id,
            order_status_type_code=action_status_code_dict.get("client")
            .get("wait_for_payment")
            .get("code"),
            order_status_type=action_status_code_dict.get("client")
            .get("wait_for_payment")
            .get("text"),
            order_operator="client",
        )
        order_product = T_Order_Product(
            product_id=product.product_id,
            order_id=new_order.order_id,
            product_name=product.product_name,
            product_count=product_count,
            price_current=product.price_current,
            duration=product.duration,
            body_parts=product.body_parts,
            photo_intro=product.photo_intro,
            server_time=next_service_time,
        )
        # 保存到order status表
        session.add(new_order_status)
        # 保存到order product表
        session.add(order_product)
        logger.info(f"保存加钟订单状态成功,{new_order_status}")
        logger.info(f"保存加钟产品成功,{product}")
        session.commit()
        return new_order.order_id


def set_tech_busy_time(session, order: T_Order):
    max_travel_time_seconds = 60 * 60  # 单程最多一个小时
    order_products = order.order_products
    assert (
        len(order_products) > 0
    ), f"no order product related to order, order_id {order.order_id}"
    order_product: T_Order_Product = order_products[0]
    duration: int = int(order_product.duration.split("分钟")[0])
    product_count = order_product.product_count
    service_time = order.service_time
    travel_time = (
        order.travel_time
        if order.travel_time < max_travel_time_seconds
        else max_travel_time_seconds
    )
    # 接单后，服务时间-1小时内不可接单
    if order.parent_order_id:
        start_time, end_time = delete_tech_busy_time(order.parent_order_id, session)
        assert (
            start_time is not None and end_time is not None
        ), f"parent order {order.parent_order_id} has no busy time"
        end_time = end_time + timedelta(minutes=product_count * duration)
    else:
        start_time = (
            service_time
            - timedelta(seconds=travel_time)
            - timedelta(minutes=60)
            - timedelta(minutes=default_travel_time_for_slot_calculation_minutes)
        )
        end_time = service_time + timedelta(minutes=product_count * duration)
    busy_time = T_Tech_Busy_Time(
        tech_user_openid=order.tech_user_id,
        parent_order_id=order.parent_order_id,
        order_id=order.order_id,
        start_time=start_time,
        end_time=end_time,
    )
    session.add(busy_time)
