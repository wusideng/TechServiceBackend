from pydantic import BaseModel


class OrderExtendServiceRequest(BaseModel):
    order_id: int
    product_id: int
    product_count: int
    user_openid: str
