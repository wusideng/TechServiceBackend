from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import asc, desc

from app.model.t_order_comment import T_Order_Comment
from app.model.t_order_status import T_Order_Status


@dataclass
class T_Order(SQLModel, table=True):
    order_id: Optional[int] = Field(default=None, primary_key=True)
    order_serial: Optional[str]
    create_order_time: datetime = Field(default_factory=datetime.now)
    update_order_time: datetime = Field(default=None)
    service_time: datetime
    # full address
    service_address: str
    service_province: str
    service_city: str
    service_district: str
    service_street: str
    service_region: str
    # 现在是门牌号，以前是去除了门牌号的地址
    service_detail_address: str
    # no longer used
    travel_mode: Optional[str]
    travel_distance: Decimal
    travel_time: Optional[int]
    travel_cost: Decimal
    nickname: Optional[str]
    payment_mode: Optional[str]
    payment_status: str
    payment_status_code: Optional[str]
    tech_user_id: str = Field(foreign_key="t_tech_user.openid")
    client_user_id: str = Field(foreign_key="t_client_user.openid")
    order_status_code_client: Optional[str]
    order_status_code_tech: Optional[str]
    order_cost: Decimal
    out_trade_no: Optional[str]
    remark: Optional[str]
    actual_fee_received: Optional[Decimal]
    coupon_value: Optional[Decimal]
    parent_order_id: Optional[int]
    actual_tech_openid: Optional[str] = Field(
        default=None, foreign_key="t_tech_user.openid"
    )
    client: Optional["T_Client_User"] = Relationship(back_populates="orders")
    tech: Optional["T_Tech_User"] = Relationship(
        back_populates="orders",
        sa_relationship_kwargs={"foreign_keys": "[T_Order.tech_user_id]"},
    )
    # 新增：实际技术人员关系
    actual_tech: Optional["T_Tech_User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[T_Order.actual_tech_openid]"}
    )
    order_products: List["T_Order_Product"] = Relationship(back_populates="order")
    order_status: List["T_Order_Status"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={
            "order_by": lambda: desc(T_Order_Status.order_status_time)
        },
    )
    coupon_id: Optional[int]
    order_comment: Optional["T_Order_Comment"] = Relationship(back_populates="order")


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_order')

# CREATE TABLE [dbo].[t_order](
# 	[order_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[order_serial] nvarchar(20) NULL,
# 	[create_order_time] datetime NOT NULL,
# 	[update_order_time] datetime NULL,
# 	[service_time] datetime NOT NULL,
# 	[service_address] nvarchar(100) NOT NULL,
# 	[service_city] nvarchar(101) NOT NULL,
# 	[service_detail_address] nvarchar(102) NOT NULL,
# 	[travel_mode] nvarchar(20) NULL,
# 	[travel_distance] decimal NOT NULL,
# 	[travel_cost] decimal NOT NULL,
#   [travel_time] int NOT NULL,
#   [nickname] nvarchar(50) NULL,
# 	[payment_mode] nvarchar(20) NULL,
# 	[payment_status] nvarchar(20) NOT NULL,
# 	[tech_user_id] nvarchar(100) NOT NULL,
# 	[client_user_id] nvarchar(100) NOT NULL,
# 	[order_cost] decimal NOT NULL,
# 	[remark] nvarchar(100) NULL,
# 	[order_status_code_client] nvarchar(100) NULL,
# 	[order_status_code_tech] nvarchar(100) NULL ) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键订单ID','SCHEMA','dbo','TABLE','t_order','COLUMN','order_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单编号','SCHEMA','dbo','TABLE','t_order','COLUMN','order_serial';
# EXEC sys.sp_addextendedproperty 'MS_Description','下单时间','SCHEMA','dbo','TABLE','t_order','COLUMN','create_order_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','更新时间','SCHEMA','dbo','TABLE','t_order','COLUMN','update_order_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','服务时间','SCHEMA','dbo','TABLE','t_order','COLUMN','service_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','服务地址','SCHEMA','dbo','TABLE','t_order','COLUMN','service_address';
# EXEC sys.sp_addextendedproperty 'MS_Description','城市','SCHEMA','dbo','TABLE','t_order','COLUMN','service_city';
# EXEC sys.sp_addextendedproperty 'MS_Description','小区','SCHEMA','dbo','TABLE','t_order','COLUMN','service_detail_address';
# EXEC sys.sp_addextendedproperty 'MS_Description','出行方式','SCHEMA','dbo','TABLE','t_order','COLUMN','travel_mode';
# EXEC sys.sp_addextendedproperty 'MS_Description','出行距离','SCHEMA','dbo','TABLE','t_order','COLUMN','travel_distance';
# EXEC sys.sp_addextendedproperty 'MS_Description','出行费用','SCHEMA','dbo','TABLE','t_order','COLUMN','travel_cost';
# EXEC sys.sp_addextendedproperty 'MS_Description','支付方式(微信，支付宝)','SCHEMA','dbo','TABLE','t_order','COLUMN','payment_mode';
# EXEC sys.sp_addextendedproperty 'MS_Description','支付状态','SCHEMA','dbo','TABLE','t_order','COLUMN','payment_status';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师ID','SCHEMA','dbo','TABLE','t_order','COLUMN','tech_user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','顾客ID','SCHEMA','dbo','TABLE','t_order','COLUMN','client_user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单费用','SCHEMA','dbo','TABLE','t_order','COLUMN','order_cost';
# EXEC sys.sp_addextendedproperty 'MS_Description','备注','SCHEMA','dbo','TABLE','t_order','COLUMN','remark';
# EXEC sys.sp_addextendedproperty 'MS_Description','备注','SCHEMA','dbo','TABLE','t_order','COLUMN','order_status_code_client';
# EXEC sys.sp_addextendedproperty 'MS_Description','备注','SCHEMA','dbo','TABLE','t_order','COLUMN','order_status_code_tech';
