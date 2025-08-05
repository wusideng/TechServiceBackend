from datetime import datetime
from typing import Tuple, Union
from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload, noload, selectinload
from sqlmodel import Session, select
from app.core.config import product_base
from app.core.util import generate_nonce_str, generate_signature, settings
from app.model.t_order import T_Order
from app.model.t_order_product import T_Order_Product
from app.model.t_tech_user import T_Tech_User
from config import enable_pay_test


def get_existing_order_and_latest_product(
    order_id: int, session: Session, user_openid: str
) -> Tuple[T_Order, T_Order_Product]:
    existing_order: T_Order = session.exec(
        select(T_Order)
        .where(T_Order.order_id == order_id)
        .options(
            joinedload(T_Order.tech),
            noload(T_Order.client),
            noload(T_Order.order_status),
            noload(T_Order.order_comment),
            noload(T_Order.order_products),
        )
    ).first()
    assert existing_order is not None, "order not found"
    assert existing_order.client_user_id == user_openid, "user openid not match"

    # 修改查询逻辑：查找order_id为指定order_id或者关联到parent_order_id为指定order_id的订单产品
    latest_product = session.exec(
        select(T_Order_Product)
        .join(T_Order, T_Order_Product.order_id == T_Order.order_id)
        .where(
            or_(
                T_Order_Product.order_id == order_id,
                T_Order.parent_order_id == order_id,
            )
        )
        .options(
            noload(T_Order_Product.order),
        )
        .order_by(desc(T_Order_Product.server_time))
        .limit(1)
    ).first()
    assert latest_product is not None, "latest product not found"
    return (existing_order, latest_product)


def generate_order_data(product_name: str, order_cost: float, user_openid: str) -> dict:
    out_trade_no = str(int(datetime.now().timestamp()))
    if enable_pay_test and user_openid in [
        "oK9p06UX2a02_b9Cn4W7cfoWjE3c",
        "oK9p06S43s67ui0VxR3-h3REu0VY",
    ]:
        total_fee = 10
    else:
        # 有时因为车费不是整数，导致order_cost*100算出来是浮点数比如19999.0，这样的数据不被微信接受
        # 因此这里必须再次转为整形，真实扯淡，微信支付的坑
        total_fee = int(order_cost * 100)
    order_data = {
        "appid": settings.APPID,
        "mch_id": settings.MCHID,
        "nonce_str": generate_nonce_str(),
        # 'body': '调理之源',
        "body": product_name,
        "out_trade_no": out_trade_no,
        # 'total_fee': 1, # 单位 分
        "total_fee": total_fee,
        "spbill_create_ip": "127.0.0.1",  # 客户端IP
        "notify_url": f"{product_base}/orders/wxpay_notify",
        "trade_type": "JSAPI",
        "openid": user_openid,
    }
    # 生成签名
    order_data["sign"] = generate_signature(order_data)
    return order_data


def generate_response_from_wx_pay_response(
    result: dict,
    order_id: int,
    order_data: dict,
):
    prepay_id = result["xml"]["prepay_id"]
    response = {
        "appId": settings.APPID,
        "timeStamp": str(int(datetime.now().timestamp())),
        "nonceStr": order_data["nonce_str"],
        "package": f"prepay_id={prepay_id}",
        "signType": "MD5",
        "paySign": generate_signature(
            {
                "appId": settings.APPID,
                "timeStamp": str(int(datetime.now().timestamp())),
                "nonceStr": order_data["nonce_str"],
                "package": f"prepay_id={prepay_id}",
                "signType": "MD5",
            }
        ),
        "order_id": order_id,
    }

    return response
