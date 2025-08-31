from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Bill(SQLModel, table=True):
    bill_id: Optional[int] = Field(default=None, primary_key=True)
    amount: Decimal
    tech_income: Decimal
    travel_cost: Decimal
    tax: Decimal
    openid: str
    user_nickname: str
    ratio: Optional[int]
    order_id: int
    work_city: str
    withdrawed: bool = False
    payment_status: Optional[str]
    time_stamp: datetime = Field(default_factory=datetime.now)


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_bill')

# CREATE TABLE [dbo].[t_bill](
#   [bill_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[amount] decimal NOT NULL,
# 	[tech_income] decimal NOT NULL,
# 	[travel_cost] decimal NOT NULL,
# 	[openid] nvarchar(20) NOT NULL,
# 	[user_nickname] [nvarchar](20) NOT NULL,
# 	[ratio] INT NULL,
# 	[order_id] INT NOT NULL,
# 	[work_city] nvarchar(20) NOT NULL,
# 	[payment_status] nvarchar(20) NOT NULL,
# 	[time_stamp] datetime NOT NULL,	) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','账单id（主键）','SCHEMA','dbo','TABLE','t_bill','COLUMN','bill_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','收入金额','SCHEMA','dbo','TABLE','t_bill','COLUMN','amount';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师收益','SCHEMA','dbo','TABLE','t_bill','COLUMN','tech_income';
# EXEC sys.sp_addextendedproperty 'MS_Description','交通费','SCHEMA','dbo','TABLE','t_bill','COLUMN','travel_cost';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师openid','SCHEMA','dbo','TABLE','t_bill','COLUMN','openid';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师昵称','SCHEMA','dbo','TABLE','t_bill','COLUMN','user_nickname';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师分成比例','SCHEMA','dbo','TABLE','t_bill','COLUMN','ratio';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单id','SCHEMA','dbo','TABLE','t_bill','COLUMN','order_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','所在城市','SCHEMA','dbo','TABLE','t_bill','COLUMN','work_city';
# EXEC sys.sp_addextendedproperty 'MS_Description','发放状态(unpaid（未发放）,paid（已发放）)','SCHEMA','dbo','TABLE','t_bill','COLUMN','payment_status';
# EXEC sys.sp_addextendedproperty 'MS_Description','入账时间','SCHEMA','dbo','TABLE','t_bill','COLUMN','time_stamp';
