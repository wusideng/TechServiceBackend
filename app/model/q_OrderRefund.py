from typing import Optional
from sqlmodel import SQLModel


class OrderRefund(SQLModel):
    orderId: str
    reason: Optional[str] = None
