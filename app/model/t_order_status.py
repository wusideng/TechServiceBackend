from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional


class T_Order_Status(SQLModel, table=True):
    order_status_id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="t_order.order_id")
    order_status_type_code: str
    order_status_type: str
    order_status_photo: Optional[str] = None
    order_status_time: datetime = Field(default_factory=datetime.now)
    order_desc: Optional[str] = None
    order_operator: str
    order: Optional["T_Order"] = Relationship(back_populates="order_status")


# CREATE TABLE [dbo].[t_order_status](
# 	[order_status_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[order_id] int NOT NULL,
# 	[order_status_type_code] nvarchar(20) NOT NULL,
# 	[order_status_type] nvarchar(20) NOT NULL,
# 	[order_status_time] datetime NOT NULL,	) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键','SCHEMA','dbo','TABLE','t_order_status','COLUMN','order_status_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单id','SCHEMA','dbo','TABLE','t_order_status','COLUMN','order_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单状态','SCHEMA','dbo','TABLE','t_order_status','COLUMN','order_status_type_code';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单状态编码','SCHEMA','dbo','TABLE','t_order_status','COLUMN','order_status_type';
# EXEC sys.sp_addextendedproperty 'MS_Description','更新时间','SCHEMA','dbo','TABLE','t_order_status','COLUMN','order_status_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单描述，主要用于顾客取消订单','SCHEMA','dbo','TABLE','t_order_status','COLUMN','order_desc';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单操作人(技师为tech, 顾客为client)','SCHEMA','dbo','TABLE','t_order_status','COLUMN','order_operator';

# code	content	comment	dict_type
# order_011	待支付	已预约待支付	order
# order_012	已支付	已预约已支付	order
# order_013	待退款	已申请退款，待退款审批通过	order
# order_014	已退款	已退款，已通过	order
# order_021	待接单	1、等待技师接单；2、等待管理员排单；3、技师拒绝接单，等待管理员排单	order
# order_022	确认接单	技师确认接单	order
# order_023	已经出发	技师已出发	order
# order_024	已经到达	技师已到达	order
# order_025	开始服务	技师开始服务	order
# order_026	服务结束	服务结束	order
# order_027	技师确认服务结束	服务结束	order
# order_028	确认离开	确认离开	order
# order_031	顾客评论	顾客评论	order
# order_032	技师评论	技师评论	order
