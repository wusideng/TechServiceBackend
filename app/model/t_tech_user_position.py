from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Tech_User_Position(SQLModel, table=True):
    tech_user_position_id: Optional[int] = Field(default=None, primary_key=True)
    tech_user_id: str
    refresh_time: datetime = Field(default_factory=datetime.now)
    lon: Decimal
    lat: Decimal
    address: str
    work_city: Optional[str] = None
    work_position: Optional[str] = None
    sub_position: Optional[str] = None
    work_range: Optional[Decimal] = None


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_tech_user_position')

# CREATE TABLE [dbo].[t_tech_user_position](
# 	[tech_user_position_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[tech_user_id] nvarchar(20) NOT NULL,
# 	[refresh_time] datetime NOT NULL,
# 	[lon] decimal NOT NULL,
# 	[lat] decimal NOT NULL,
# 	[address] nvarchar(200) NOT NULL,
# 	[work_city] nvarchar(200) NULL,
# 	[work_position] nvarchar(200) NULL,
# 	[sub_position] nvarchar(200) NULL,
# 	[work_range] decimal NULL	) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','tech_user_position_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师ID（openid）','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','tech_user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','更新时间','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','refresh_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','经度','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','lon';
# EXEC sys.sp_addextendedproperty 'MS_Description','纬度','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','lat';
# EXEC sys.sp_addextendedproperty 'MS_Description','位置','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','address';
# EXEC sys.sp_addextendedproperty 'MS_Description','工作城市','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','work_city';
# EXEC sys.sp_addextendedproperty 'MS_Description','当前位置','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','work_position';
# EXEC sys.sp_addextendedproperty 'MS_Description','位置替身','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','sub_position';
# EXEC sys.sp_addextendedproperty 'MS_Description','工作范围(km)','SCHEMA','dbo','TABLE','t_tech_user_position','COLUMN','work_range';
