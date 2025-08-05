from typing import List, Optional
from typing_extensions import NotRequired, TypedDict


class FundSource(TypedDict):
    """退款出资账户及金额信息"""

    account: str  # 账户类型
    amount: int  # 金额，单位为分


class PromotionDetail(TypedDict):
    """优惠退款详情"""

    promotion_id: str  # 券ID
    scope: str  # 优惠范围 GLOBAL/SINGLE
    type: str  # 优惠类型 CASH/NOCASH
    amount: int  # 代金券面额
    refund_amount: int  # 优惠退款金额


class GoodsDetail(TypedDict):
    """退款商品信息"""

    merchant_goods_id: str  # 商户侧商品编码
    wechatpay_goods_id: NotRequired[Optional[str]]  # 微信侧商品编码
    goods_name: NotRequired[Optional[str]]  # 商品名称
    unit_price: int  # 商品单价
    refund_amount: int  # 商品退款金额
    refund_quantity: int  # 商品退货数量


class Amount(TypedDict):
    """金额信息"""

    total: int  # 订单总金额,单位是分
    refund: int  # 退款金额，单位是分
    payer_total: int  # 用户实际支付金额
    payer_refund: int  # 用户退款金额
    settlement_refund: int  # 应结退款金额
    settlement_total: int  # 应结订单金额
    discount_refund: int  # 优惠退款金额
    currency: str  # 退款币种
    refund_fee: Optional[int] = None  # 手续费退款金额


Amount.__annotations__["from"] = NotRequired[Optional[List[FundSource]]]


class RefundResponse(TypedDict):
    """微信支付退款响应"""

    refund_id: str  # 微信支付退款单号
    out_refund_no: str  # 商户退款单号
    transaction_id: str  # 微信支付订单号
    out_trade_no: str  # 商户订单号
    channel: str  # 退款渠道
    user_received_account: str  # 退款入账账户
    success_time: NotRequired[Optional[str]]  # 退款成功时间
    create_time: str  # 退款创建时间
    status: str  # 退款状态
    funds_account: str  # 资金账户
    amount: Amount  # 金额信息
    promotion_detail: NotRequired[Optional[List[PromotionDetail]]]  # 优惠退款详情
    goods_detail: NotRequired[Optional[List[GoodsDetail]]]  # 退款商品


class Resource(TypedDict):
    algorithm: str
    original_type: str
    ciphertext: str
    associated_data: NotRequired[Optional[str]]
    nonce: str


class RefundNotifyResponse(TypedDict):
    id: str
    create_time: str
    event_type: str
    summary: str
    resource_type: str
    resource: Resource
