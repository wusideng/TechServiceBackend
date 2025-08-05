from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import desc


class TechAddress(SQLModel, table=True):
    """用户地址模型"""

    __tablename__ = "t_tech_user_addresses"

    id: Optional[int] = Field(default=None, primary_key=True)
    openid: str = Field(default=None, description="微信openid")
    is_default: bool = Field(default=False, description="是否为默认地址")

    address: Optional[str] = Field(
        default=None, description="完整的地址，包含省市县小区门牌号等"
    )
    province: Optional[str] = Field(default=None, description="用户所在省份")
    city: str = Field(description="用户所在城市")
    district: str = Field(description="用户所在区域")
    street: str = Field(description="用户所在街道")
    region: str = Field(description="用户所在小区")
    detail_address: Optional[str] = Field(description="门牌号")
    lon: float = Field(description="经度")
    lat: float = Field(description="纬度")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default=None)


# CREATE TABLE home_massage_dev.dbo.t_tech_user_addresses (
# 	id int IDENTITY(1,1) NOT NULL,
# 	openid nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
# 	is_default bit DEFAULT 0 NOT NULL,
# 	address nvarchar(500) COLLATE Chinese_PRC_CI_AS NULL,
# 	province nvarchar(50) COLLATE Chinese_PRC_CI_AS NOT NULL,
# 	city nvarchar(50) COLLATE Chinese_PRC_CI_AS NOT NULL,
# 	district nvarchar(50) COLLATE Chinese_PRC_CI_AS NOT NULL,
# 	street nvarchar(50) COLLATE Chinese_PRC_CI_AS NOT NULL,
# 	region nvarchar(200) COLLATE Chinese_PRC_CI_AS NOT NULL,
# 	detail_address nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
# 	lon decimal(9,6) NOT NULL,
# 	lat decimal(9,6) NOT NULL,
# 	create_time datetime DEFAULT getdate() NOT NULL,
# 	update_time datetime NULL,
# 	CONSTRAINT PK_t_tech_user_address_id PRIMARY KEY (id)
# );
