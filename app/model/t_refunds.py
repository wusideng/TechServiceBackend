from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Refunds(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)  # 自增主键
    refund_id: str = Field(max_length=50, nullable=False)  # 微信退款单号
    order_id: str = Field(
        max_length=50, nullable=False, foreign_key="t_order.order_id"
    )  # 商户订单号（外键关联订单表）
    applied_refund_amount: float = Field(nullable=False)  # 申请退款金额
    actual_refund_amount: float = Field(nullable=False)  # 实际退款金额
    refund_status: str = Field(
        max_length=20, nullable=False
    )  # 退款状态（PROCESSING, SUCCESS, CHANGE）
    refund_status_code: str = Field(max_length=20, nullable=True)  # 退款状态码
    refund_reason: Optional[str] = Field(max_length=255)  # 退款原因（可选字段）
    refund_time: Optional[str] = Field(default=None)  # 退款完成时间（可选字段）
    refund_error_code: Optional[str] = Field(max_length=50)  # 退款错误码（可选字段）
    refund_error_code_desc: Optional[str] = Field(
        max_length=100
    )  # 退款错误码描述（可选字段）
    out_refund_no: Optional[str] = Field(
        max_length=50
    )  # 【商户退款单号】 商户系统内部的退款单号，商户系统内部唯一，只能是数字、大小写字母_-|*@ ，同一商户退款单号多次请求只退一笔。不可超过64个字节数。
    is_notified: Optional[bool] = Field(
        default=False
    )  # 是否已通知，对应 SQL Server 中的 bit 类型，可为空

    create_time: Optional[datetime] = Field(default_factory=datetime.now)  # 创建时间
    update_time: Optional[datetime] = Field(default_factory=datetime.now)  # 更新时间
