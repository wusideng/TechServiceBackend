from typing import Optional
from pydantic import BaseModel


class NotificationRequest(BaseModel):
    return_code: str
    return_msg: Optional[str] = None
    appid: Optional[str] = None
    mch_id: Optional[str] = None
    nonce_str: Optional[str] = None
    req_info: Optional[str] = None


class ReqInfo(BaseModel):
    transaction_id: str
    out_trade_no: str
    refund_id: str
    out_refund_no: str
    total_fee: int
    settlement_total_fee: Optional[int] = None
    refund_fee: int
    settlement_refund_fee: int
    # SUCCESS-退款成功
    # CHANGE-退款异常
    # REFUNDCLOSE—退款关闭
    refund_status: str
    success_time: Optional[str] = None
    refund_recv_accout: str
    refund_account: str
    refund_request_source: str
    cash_refund_fee: int
