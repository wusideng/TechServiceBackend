from pydantic import BaseModel


class TagOrderReplaceTech(BaseModel):
    actual_tech_openid: str
    order_id: int
