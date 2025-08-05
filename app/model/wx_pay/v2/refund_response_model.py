from typing import List, Optional
from typing_extensions import NotRequired, TypedDict


class RefundResponse(TypedDict):
    """微信支付退款响应"""

    # 非业务字段
    return_code: str  # 返回状态码
    return_msg: NotRequired[Optional[str]]  # 返回信息

    # 业务字段
    result_code: str  # 业务结果
    err_code: NotRequired[Optional[str]]  # 错误码
    err_code_des: NotRequired[Optional[str]]  # 错误描述
    appid: str  # 应用ID
    mch_id: str  # 商户号
    nonce_str: str  # 随机字符串
    sign: str  # 签名
    transaction_id: str  # 微信支付订单号
    out_trade_no: str  # 商户订单号
    out_refund_no: str  # 商户退款单号
    refund_id: str  # 微信退款单号
    refund_fee: int  # 退款金额
    settlement_refund_fee: NotRequired[
        Optional[int]
    ]  # 去掉非充值代金券退款金额后的退款金额，退款金额=申请退款金额-非充值代金券退款金额，退款金额<=申请退款金额
    total_fee: int  # 订单金额
    settlement_total_fee: NotRequired[
        Optional[int]
    ]  # 去掉非充值代金券金额后的订单总金额，应结订单金额=订单金额-非充值代金券金额，应结订单金额<=订单金额。
    fee_type: NotRequired[Optional[str]]  # 货币种类
    cash_fee: int  # 现金支付金额，单位为分，只能为整数，详见支付金额
    cash_fee_type: NotRequired[Optional[str]]  # 货币类型
    cash_refund_fee: NotRequired[
        Optional[int]
    ]  # 现金退款金额，单位为分，只能为整数，详见支付金额


class RefundNotifyResponse(TypedDict):
    appid: str  # 应用ID
    mch_id: str  # 商户号
    nonce_str: str  # 随机字符串
    req_info: str  # 加密信息请用商户密钥进行解密，详见解密方式


class DecodedRefundNotifyResponse(TypedDict):
    transaction_id: str  # 微信支付订单号
    out_trade_no: str  # 商户订单号
    refund_id: str  # 微信退款单号
    out_refund_no: str  # 商户退款单号
    total_fee: int  # 订单金额
    settlement_total_fee: NotRequired[Optional[int]]  # 应结订单金额
    refund_fee: int  # 申请退款金额
    settlement_refund_fee: NotRequired[Optional[int]]  # 退款金额
    refund_status: str  # 退款状态
    success_time: NotRequired[Optional[str]]  # 退款成功时间
    refund_recv_accout: str  # 退款入账账户
    refund_account: str  # 退款资金来源
    refund_request_source: str  # 退款请求来源
    cash_refund_fee: int  # 现金退款金额,退款给用户的金额，不包含所有优惠券金额
