from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Coupon(SQLModel, table=True):
    coupon_id: Optional[int] = Field(default=None, primary_key=True)
    open_id: str
    amount: int
    condition: int
    project: Optional[str]
    expiration_time: datetime
    grant_time: datetime = Field(default_factory=datetime.now)
    grant_city: str
    coupon_type: str
    msg: str
    coupon_status: Optional[str]
    activity_id: Optional[int]


# CREATE TABLE [dbo].[t_coupon](
#     [coupon_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[open_id] nvarchar(50) NOT NULL,
# 	[amount] nvarchar(50) NOT NULL,
# 	[condition] int NOT NULL,
# 	[project] nvarchar(50) NULL,
# 	[expiration_time] datetime NOT NULL,
# 	[grant_time] datetime NOT NULL,
#     [grant_city] nvarchar(50) NOT NULL,
#     [coupon_type] nvarchar(50) NOT NULL,
#     ) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','优惠券id','SCHEMA','dbo','TABLE','t_coupon','COLUMN','coupon_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户opent_id','SCHEMA','dbo','TABLE','t_coupon','COLUMN','open_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','优惠券面值','SCHEMA','dbo','TABLE','t_coupon','COLUMN','amount';
# EXEC sys.sp_addextendedproperty 'MS_Description','优惠券最小使用金额','SCHEMA','dbo','TABLE','t_coupon','COLUMN','condition';
# EXEC sys.sp_addextendedproperty 'MS_Description','优惠券覆盖项目(按摩，保洁，维修，健身)','SCHEMA','dbo','TABLE','t_coupon','COLUMN','project';
# EXEC sys.sp_addextendedproperty 'MS_Description','到期时间','SCHEMA','dbo','TABLE','t_coupon','COLUMN','expiration_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','发放时间','SCHEMA','dbo','TABLE','t_coupon','COLUMN','grant_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','发放城市','SCHEMA','dbo','TABLE','t_coupon','COLUMN','grant_city';
# EXEC sys.sp_addextendedproperty 'MS_Description','优惠券类型(新人，老用户，节假日)','SCHEMA','dbo','TABLE','t_coupon','COLUMN','coupon_type';
# EXEC sys.sp_addextendedproperty 'MS_Description','优惠券说明','dbo','TABLE','t_coupon','COLUMN','msg';
# EXEC sys.sp_addextendedproperty 'MS_Description','优惠券状态(已使用 used, 已过期 past)','SCHEMA','dbo','TABLE','t_coupon','COLUMN','coupon_status';
