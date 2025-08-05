from sqlmodel import SQLModel
from typing import List

from app.model.t_order import T_Order
from app.model.t_order_product import T_Order_Product
from app.model.t_coupon import T_Coupon


class OrderCreate(SQLModel):
    order: T_Order
    product: T_Order_Product


class AddCouponeRequest(SQLModel):
    coupons: List[T_Coupon]


class AddFackCommentRequest(SQLModel):
    client_score_to_tech: float
    client_comment: str
