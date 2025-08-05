from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import desc


class T_User_Follows(SQLModel, table=True):
    """用户关注技师模型"""

    __tablename__ = "t_user_follows"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_openid: int = Field(foreign_key="t_client_user.openid")
    tech_openid: int = Field(foreign_key="t_tech_user.openid")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)
