from typing import Optional
from pydantic import BaseModel


class PaymentNotifyRequestOnReturnCodeSuccess(BaseModel):
    return_code: str
    return_msg: Optional[str] = None
    appid: str
    mch_id: str
    device_info: Optional[str] = None
    nonce_str: str
    sign: str
    sign_type: Optional[str] = None
    result_code: str  # SUCCESS/FAIL
    err_code: Optional[str] = None
    err_code_des: Optional[str] = None
    openid: Optional[str]
    trade_type: Optional[str]
    bank_type: Optional[str]
    total_fee: int
    settlement_total_fee: Optional[int] = None
    fee_type: Optional[str] = None
    cash_fee: Optional[int]
    cash_fee_type: Optional[str] = None
    transaction_id: Optional[str] = None
    out_trade_no: str
    # 实际到账时间
    time_end: str
