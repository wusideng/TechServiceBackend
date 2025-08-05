from typing import List
from pydantic import BaseModel


class TakeCouponsFromActivity(BaseModel):
    openid: str
    activity_id: int
    city: str


class CouponItem(BaseModel):
    coupon_value: int
    amount: int


class SendCompensateCoupons(BaseModel):
    client_user_openid: str
    order_id: int
    coupons: List[CouponItem]
