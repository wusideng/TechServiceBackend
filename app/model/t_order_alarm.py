from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Order_Alarm(SQLModel, table=True):
    alarm_id: Optional[int] = Field(default=None, primary_key=True)
    alarm_status: str
    order_id: int
    time_stamp: datetime
    information: str
    ramark: str


# CREATE TABLE [dbo].[t_order_alarm](
#   [alarm_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[alarm_status] nvarchar(20) NOT NULL,
# 	[order_id] INT NOT NULL,
# 	[time_stamp] datetime NOT NULL,
# 	[information] nvarchar(500) NOT NULL,
# 	[ramark] nvarchar(500) NOT NULL,	) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键','SCHEMA','dbo','TABLE','t_order_alarm','COLUMN','alarm_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','报警状态，待处理，处理中，处理结束','SCHEMA','dbo','TABLE','t_order_alarm','COLUMN','alarm_status';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单ID','SCHEMA','dbo','TABLE','t_order_alarm','COLUMN','order_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','报警时间','SCHEMA','dbo','TABLE','t_order_alarm','COLUMN','time_stamp';
# EXEC sys.sp_addextendedproperty 'MS_Description','报警信息','SCHEMA','dbo','TABLE','t_order_alarm','COLUMN','information';
# EXEC sys.sp_addextendedproperty 'MS_Description','备注','SCHEMA','dbo','TABLE','t_order_alarm','COLUMN','ramark';
