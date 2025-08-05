from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Client_User_Position(SQLModel, table=True):
    client_user_position_id: Optional[int] = Field(default=None, primary_key=True)
    client_openid: Optional[str] = Field(nullable=True)
    refresh_time: datetime = Field(default_factory=datetime.now)
    lon: Decimal
    lat: Decimal
    address: Optional[str] = None
    city: Optional[str] = None
    detail_address: Optional[str] = None


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_client_user_positon')

# CREATE TABLE [dbo].[t_client_user_positon](
#   [client_user_position_id] INT IDENTITY(1,1) PRIMARY KEY,
#   [client_user_id] nvarchar(100)NOT NULL,
#   [refresh_time] datetime NOT NULL,
#   [lon] decimal(9, 6) NOT NULL,
#   [lat] decimal(9, 6) NOT NULL,
#   [address] nvarchar(200)NULL,
#   [city] nvarchar(20)NULL,
#   [detail_address] nvarchar(200)NULL,
# ) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','work_position_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师ID(openid)','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','client_user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','更新时间','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','refresh_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','经度坐标','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','lon';
# EXEC sys.sp_addextendedproperty 'MS_Description','纬度坐标','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','lat';
# EXEC sys.sp_addextendedproperty 'MS_Description','地址','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','address';
# EXEC sys.sp_addextendedproperty 'MS_Description','城市','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','city';
# EXEC sys.sp_addextendedproperty 'MS_Description','当前位置','SCHEMA','dbo','TABLE','t_client_user_positon','COLUMN','detail_address';
