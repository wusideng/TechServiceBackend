from dataclasses import dataclass
from pydantic import BaseModel

from .q_OrderCreate import OrderCreate


@dataclass
class OrderPayRequest(BaseModel):
    prodname: str
    clientOpenId: str
    # total_fee: int
    order_product_info: OrderCreate


@dataclass
class ContinueToPayRequest(BaseModel):
    user_id: str
    order_id: int
