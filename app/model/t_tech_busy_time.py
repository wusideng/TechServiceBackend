from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import desc


class T_Tech_Busy_Time(SQLModel, table=True):
    """技师接单后忙碌时间"""

    __tablename__ = "t_tech_busy_time"

    id: Optional[int] = Field(default=None, primary_key=True)
    tech_user_openid: str = Field(foreign_key="t_tech_user.openid")
    order_id: int = Field(foreign_key="t_order.order_id")
    parent_order_id: int = Field(nullable=True)
    start_time: datetime = Field(nullable=False)
    end_time: datetime = Field(nullable=False)
    create_time: datetime = Field(default_factory=datetime.now)
