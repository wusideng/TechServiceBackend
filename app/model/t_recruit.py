from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import desc


class T_Recruit(SQLModel, table=True):
    """城市代理/技师招募"""

    __tablename__ = "t_recruit"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="姓名")
    phone: str = Field(max_length=100, description="手机号码")
    city: str = Field(max_length=100, description="城市")
    age: Optional[int] = Field(default=None, description="年龄")
    gender: Optional[str] = Field(default=None, max_length=10, description="性别:男/女")
    message: Optional[str] = Field(default=None, max_length=500, description="留言")
    recruit_type: str = Field(
        max_length=20, description="招募类型(tech-技师/partner-城市代理)"
    )
    create_time: datetime = Field(default_factory=datetime.now, description="申请时间")
    has_contacted: bool = Field(default=False, description="是否已联系:0-否/1-是")
    remark: str = Field(max_length=100, description="备注")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
