from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class T_Sms_Invite(SQLModel, table=True):
    """短信验证码"""

    __tablename__ = "t_sms_invite"

    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(max_length=11, description="手机号码", index=True)
    client_openid: str = Field(description="客户OpenId")
    tech_openid: str = Field(description="技术OpenId")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
