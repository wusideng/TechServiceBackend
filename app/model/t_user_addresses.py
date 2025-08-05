from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import desc


class UserAddress(SQLModel, table=True):
    """用户地址模型"""

    __tablename__ = "t_client_user_addresses"

    id: Optional[int] = Field(default=None, primary_key=True)
    openid: Optional[str] = Field(default=None, description="微信openid")
    name: str = Field(description="用户姓名")
    phone: str = Field(description="用户电话")
    is_default: bool = Field(default=False, description="是否为默认地址")

    address: Optional[str] = Field(
        default=None, description="完整的地址，包含省市县小区门牌号等"
    )
    province: Optional[str] = Field(default=None, description="用户所在省份")
    city: str = Field(description="用户所在城市")
    district: str = Field(description="用户所在区域")
    street: str = Field(description="用户所在街道")
    region: str = Field(description="用户所在小区")
    detail_address: str = Field(description="门牌号")
    lon: float = Field(description="经度")
    lat: float = Field(description="纬度")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default=None)
