import httpx
from starlette.responses import Response
import xmltodict
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.config import product_base
from app.core.database import engine, get_session
from app.core.util import (
    decrypt_req_info,
    generate_nonce_str,
    generate_signature,
    send_async_request_with_cert,
)
from app.model.q_OrderRefund import OrderRefund
from app.model.t_order import T_Order
from app.model.t_order_status import T_Order_Status
from app.core.config import action_status_code_dict
from app.model.t_refunds import T_Refunds
from app.model.wx_pay.v2.refund_notify_request_model import NotificationRequest, ReqInfo
from app.model.wx_pay.v2.refund_request_model import RefundRequest
from app.model.wx_pay.v2.refund_response_model import RefundResponse
from app.routers.order_pay import T_Tech_Busy_Time, delete_tech_busy_time
from logger import logger
from config import app_id, mch_id, key, server_port

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.post("/refund")
async def refund_request(
    orderRefund: OrderRefund, session: Session = Depends(get_session)
):
    orderId = orderRefund.orderId
    reason = orderRefund.reason
    try:
        existing_order = session.exec(
            select(T_Order).where(T_Order.order_id == orderId)
        ).first()
        delete_tech_busy_time(orderId, session)
        if (
            existing_order.out_trade_no == None
            or existing_order.payment_status_code
            == action_status_code_dict["client"]["wait_for_payment"]["code"]
            or existing_order.payment_status_code
            == action_status_code_dict["client"]["payment_failed"]["code"]
        ):
            payment_status_code = action_status_code_dict["client"][
                "cancel_before_pay"
            ]["code"]
            payment_status = action_status_code_dict["client"]["cancel_before_pay"][
                "text"
            ]
            existing_order.payment_status_code = payment_status_code
            existing_order.payment_status = payment_status
            logger.info("订单未支付，无法退款")
            new_order_status = T_Order_Status(
                order_id=existing_order.order_id,
                order_status_type_code=payment_status_code,
                order_status_type=payment_status,
                order_operator="client",
            )
            session.add(new_order_status)
            session.commit()
            return {"msg": "订单已取消"}
        logger.info(
            f"existing_order - status: {existing_order.payment_status}, trade_no: {existing_order.out_trade_no}"
        )
        assert existing_order.actual_fee_received > 0, "no actual fee received"
        tech_status = existing_order.order_status_code_tech
        client_status = existing_order.order_status_code_client
        payment_status_code = existing_order.payment_status_code
        if payment_status_code == action_status_code_dict["client"]["refunded"]["code"]:
            logger.info("订单已退款，无法再次退款")
            return {"msg": "订单已退款，无法再次退款"}
        if not tech_status:
            tech_status = action_status_code_dict["tech"]["wait_for_take_order"]["code"]
        # 技师已经开始服务
        if (
            tech_status
            not in [
                action_status_code_dict["tech"]["wait_for_take_order"]["code"],
                action_status_code_dict["tech"]["confirm_take_order"]["code"],
                action_status_code_dict["tech"]["has_on_the_way"]["code"],
                action_status_code_dict["tech"]["has_arrived"]["code"],
            ]
            or client_status == action_status_code_dict["client"]["service_end"]["code"]
        ):
            # 此种情况手工退钱，涉及纠纷，暂时不做微信的自动订单退款,但是会先记录到数据库中
            client_refund_text = action_status_code_dict["client"]["refund_auditing"][
                "text"
            ]
            client_refund_code = action_status_code_dict["client"]["refund_auditing"][
                "code"
            ]
            existing_order.payment_status = client_refund_text
            existing_order.payment_status_code = client_refund_code
            # existing_order.order_status_code_client = client_refund_code
            new_order_status = T_Order_Status(
                order_id=existing_order.order_id,
                order_status_type_code=client_refund_code,
                order_status_type=client_refund_text,
                order_operator="client",
            )
            session.add(new_order_status)
            session.commit()
            return {"msg": "正在审核退款申诉，请联系商户进行处理"}
        # 技师未出发
        if tech_status in [
            action_status_code_dict["tech"]["wait_for_take_order"]["code"],
            action_status_code_dict["tech"]["confirm_take_order"]["code"],
        ]:
            refund_amount = existing_order.actual_fee_received
        # 技师已经出发，但未开始服务
        elif tech_status in [
            action_status_code_dict["tech"]["has_on_the_way"]["code"],
            action_status_code_dict["tech"]["has_arrived"]["code"],
        ]:
            refund_amount = (
                existing_order.actual_fee_received
                - existing_order.travel_cost * 100 * 2
            )
        assert (
            refund_amount <= existing_order.actual_fee_received
        ), "refund amount is greater than order cost"

        client_refund_text = action_status_code_dict["client"][
            "refund_quest_send_to_3rd_party"
        ]["text"]
        client_refund_code = action_status_code_dict["client"][
            "refund_quest_send_to_3rd_party"
        ]["code"]
        existing_order.payment_status = client_refund_text
        existing_order.payment_status_code = client_refund_code
        # existing_order.order_status_code_client = client_refund_code
        new_order_status = T_Order_Status(
            order_id=existing_order.order_id,
            order_status_type_code=client_refund_code,
            order_status_type=client_refund_text,
            order_operator="client",
        )
        session.add(new_order_status)
        new_refund = T_Refunds(
            order_id=existing_order.order_id,
            applied_refund_amount=refund_amount,
            refund_reason=reason,
            refund_status_code=client_refund_code,
            refund_status=client_refund_text,
            out_refund_no=generate_out_refund_no(existing_order.order_id),
            is_notified=False,
        )
        session.add(new_refund)
        session.commit()

        order_info: RefundRequest = {
            "appid": app_id,
            "mch_id": mch_id,
            "nonce_str": generate_nonce_str(),
            "out_trade_no": str(existing_order.out_trade_no),
            "out_refund_no": generate_out_refund_no(existing_order.order_id),
            "total_fee": int(existing_order.actual_fee_received),
            "refund_fee": int(refund_amount),
            "refund_desc": reason,
            "notify_url": f"{product_base}/orders/refund_notify",
        }
        order_info["sign"] = generate_signature(order_info)
        logger.info(order_info)
        result = await refund_request_v2(order_info)
        return_code = result["xml"]["return_code"]
        # 注意这里是return_code不是result_code,前者是http响应code，后者是业务code
        logger.info(f"get refund response from wechat: {result}")
        assert return_code == "SUCCESS", "response from 3rd party is not success"
        payment_status_info = create_refund_from_response_result(
            result["xml"],
            session,
            existing_order.order_id,
        )
        logger.info(f"get calculated payment_status_info:{payment_status_info}")
        # 状态不为退款中，需要更新状态
        # with Session(engine) as session:
        existing_order.payment_status = payment_status_info["payment_status"]
        existing_order.payment_status_code = payment_status_info["payment_status_code"]
        new_order_status = T_Order_Status(
            order_id=existing_order.order_id,
            order_status_type_code=payment_status_info["payment_status_code"],
            order_status_type=payment_status_info["payment_status"],
            order_operator="wxpay",
        )
        session.add(new_order_status)
        session.commit()
        return {
            "payment_status_code": payment_status_info["payment_status_code"],
            "payment_status": payment_status_info["payment_status"],
        }
    except Exception as e:
        logger.exception(e)
        # raise HTTPException(status_code=401, detail="other error.")
        return {"msg": "退款异常，请联系商户进行退款", "error": str(e)}


async def refund_request_v2(refundRequestInfo: dict):
    try:
        response_refund: httpx.Response = await send_async_request_with_cert(
            "https://api.mch.weixin.qq.com/secapi/pay/refund", refundRequestInfo
        )
        logger.info(f"response_refund={response_refund.content}")
        result = xmltodict.parse(response_refund.content)
        logger.info(f"parsed result={result}")
        return result
    except Exception as e:
        logger.error(e)
        raise Exception(e)


@router.post("/refund_notify")
async def refund_request_v2_notify(request: Request):
    notify_data = await request.body()
    notify_info = xmltodict.parse(notify_data.decode("utf-8"))
    logger.info(f"收到微信退款通知: {notify_info}")
    if notify_info["xml"]["return_code"] == "SUCCESS":
        # xml_content = xmltodict.unparse(normal_return)
        notify_info = NotificationRequest(**notify_info["xml"])
        req_info = decrypt_req_info(notify_info.req_info, key)
        req_info = ReqInfo(**req_info)
        logger.info(f"req_info: {req_info}")
        refund_id = req_info.refund_id
        refund_status = req_info.refund_status
        actual_refund_fee = req_info.refund_fee
        out_refund_no = req_info.out_refund_no
        success_time = req_info.success_time
        # 以上字段在return_code为SUCCESS时有
        payment_status_info = get_payment_status_from_refund_status(refund_status)
        payment_status = payment_status_info["payment_status"]
        payment_status_code = payment_status_info["payment_status_code"]
        with Session(engine) as session:
            statement = select(T_Refunds).where(
                T_Refunds.out_refund_no == out_refund_no
            )
            existing_refund = session.exec(statement).first()
            assert existing_refund is not None, "退款记录不存在"
            # 更新退款记录
            if existing_refund.is_notified:
                logger.info("this is possibly a duplicate notification of refund")
                xml_content = xmltodict.unparse(
                    {"xml": {"return_code": "SUCCESS", "return_msg": "ok"}}
                )
                return Response(content=xml_content, media_type="text/xml")
            else:
                statement_order = select(T_Order).where(
                    T_Order.order_id == existing_refund.order_id
                )
                existing_order = session.exec(statement_order).first()
                assert existing_order is not None, "订单不存在"
                if refund_status == "SUCCESS":
                    existing_refund.refund_time = success_time
                    existing_refund.actual_refund_amount = actual_refund_fee
                existing_refund.refund_id = refund_id
                existing_refund.refund_status = payment_status
                existing_refund.refund_status_code = payment_status_code
                existing_refund.is_notified = True
                session.commit()
                existing_order.payment_status = payment_status
                existing_order.payment_status_code = payment_status_code
                session.commit()
                new_order_status = T_Order_Status(
                    order_id=existing_order.order_id,
                    order_status_type_code=payment_status_code,
                    order_status_type=payment_status,
                    order_operator="wxpay",
                )
                session.add(new_order_status)
                session.commit()
    xml_content = xmltodict.unparse(
        {"xml": {"return_code": "SUCCESS", "return_msg": "ok"}}
    )
    return Response(content=xml_content, media_type="text/xml")


def create_refund_from_response_result(
    result: RefundResponse,
    session: Session,
    order_id: int,
):
    """
    创建 T_Refunds 表中的退款记录，基于退款请求的 response。
    v2接口
    SUCCESS: 退款成功
    FAIL: 退款处理中
    """
    try:
        # 提取必要字段
        # return_code为SUCCESS 才进入这个方法
        result_code = result["result_code"]  # 退款状态
        # result_code只有SUCCESS和FAIL两种
        # w微信成功受理请求
        if result_code == "SUCCESS":
            payment_status_info = {
                "payment_status": action_status_code_dict["client"]["wait_for_refund"][
                    "text"
                ],
                "payment_status_code": action_status_code_dict["client"][
                    "wait_for_refund"
                ]["code"],
            }
            # 这里refund_status只能说明微信已经受理，不能说明退款到账
            refund_id = result["refund_id"]  # 微信退款单号
            out_refund_no = result["out_refund_no"]  # 商户退款单号
            actual_refund_amount = result["refund_fee"]  # 退款金额
            # 查询数据库中是否已有该退款记录
            statement = select(T_Refunds).where(
                T_Refunds.out_refund_no == out_refund_no
            )
            existing_refund = session.exec(statement).first()
            assert existing_refund is not None, "退款记录不存在"
            # 因为是异步的，存在通知先到的可能性，实际测试中发生了
            if existing_refund.is_notified:
                # 已经收到通知了，直接返回状态
                logger.info(
                    f"退款response收到,refund_id: {refund_id}, result_code：{result_code}"
                )
                return {
                    "payment_status": existing_refund.refund_status,
                    "payment_status_code": existing_refund.refund_status_code,
                }
                # refund_record.actual_refund_amount = actual_refund_amount
            else:
                # 还未收到通知，先更新，状态为退款中
                # refund_id之前没有
                existing_refund.refund_id = refund_id
                existing_refund.actual_refund_amount = actual_refund_amount
                existing_refund.refund_status = payment_status_info["payment_status"]
                existing_refund.refund_status_code = payment_status_info[
                    "payment_status_code"
                ]
                # session在方法外commit
        else:
            # 微信受理失败
            payment_status_info = {
                "payment_status": action_status_code_dict["client"]["refund_fail"][
                    "text"
                ],
                "payment_status_code": action_status_code_dict["client"]["refund_fail"][
                    "code"
                ],
            }
            # result_code is fail
            logger.info(f"退款response失败，order_id: {order_id}")
            statement = select(T_Refunds).where(T_Refunds.order_id == order_id)
            existing_refund = session.exec(statement).first()
            existing_refund.refund_status = payment_status_info["payment_status"]
            existing_refund.refund_status_code = payment_status_info[
                "payment_status_code"
            ]
            existing_refund.refund_error_code = result.get("err_code")
            existing_refund.refund_error_code_desc = result.get("err_code_des")

        return payment_status_info

    except Exception as e:
        return {"error": e}


def get_payment_status_from_refund_status(refund_status: str) -> str:
    """
    根据退款状态获取支付状态,在V2接口中，只有SUCCESS和FAIL两种状态
    """
    if refund_status == "SUCCESS":
        payment_status = (action_status_code_dict["client"]["refunded"]["text"],)
        payment_status_code = (action_status_code_dict["client"]["refunded"]["code"],)

    elif refund_status == "CHANGE":
        payment_status = action_status_code_dict["client"]["refund_abnormal"]["text"]
        payment_status_code = action_status_code_dict["client"]["refund_abnormal"][
            "code"
        ]
    else:
        payment_status = action_status_code_dict["client"]["refund_closed"]["text"]
        payment_status_code = action_status_code_dict["client"]["refund_closed"]["code"]
    return {
        "payment_status": payment_status,
        "payment_status_code": payment_status_code,
    }


def generate_out_refund_no(order_id: int):
    """
    生成商户退款单号
    """
    return f"{order_id}-{server_port}"
