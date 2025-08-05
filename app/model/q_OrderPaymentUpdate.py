from typing import Optional
from pydantic import BaseModel


class OrderPaymentUpdateRequest(BaseModel):
    order_id: int
    payment_status: str
    payment_status_code: str
    coupon_id: Optional[int] = None
