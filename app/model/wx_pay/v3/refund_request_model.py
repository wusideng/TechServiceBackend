from typing import List, Optional
from typing_extensions import NotRequired, TypedDict


class Amount(TypedDict):
    """金额信息"""

    total: int  # 订单总金额,单位是分
    refund: int  # 退款金额，单位是分
    currency: str  # 退款币种


class RefundRequest(TypedDict):
    out_trade_no: str
    out_refund_no: str
    reason: NotRequired[Optional[str]]
    notify_url: NotRequired[Optional[str]]
    amount: Amount
