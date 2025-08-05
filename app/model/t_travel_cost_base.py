from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Travel_Cost_Base(SQLModel, table=True):
    __tablename__ = "t_travel_cost_base"

    id: Optional[int] = Field(default=None, primary_key=True)
    base_price: Decimal
    base_distance_km: Decimal
    price_per_km_daytime: Decimal
    price_per_km_nighttime: Optional[Decimal] = None
    night_hour: Optional[int] = None
    city: str
    create_time: datetime = Field(default_factory=datetime.now)


# CREATE TABLE [dbo].[t_travel_cost_base](
#     [id] INT IDENTITY(1,1) PRIMARY KEY,
#     [base_price] DECIMAL(10,2) NOT NULL,
#     [base_distance_km] DECIMAL(5,2) NOT NULL,
#     [price_per_km_daytime] DECIMAL(5,2) NOT NULL,
#     [price_per_km_nighttime] DECIMAL(5,2) NULL,
#     [night_hour] INT NULL,
#     [city] NVARCHAR(50) NOT NULL,
#     [create_time] DATETIME NOT NULL DEFAULT GETDATE()
# ) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键ID','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','id';
# EXEC sys.sp_addextendedproperty 'MS_Description','起步价(元)','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','base_price';
# EXEC sys.sp_addextendedproperty 'MS_Description','起步公里数(公里)','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','base_distance_km';
# EXEC sys.sp_addextendedproperty 'MS_Description','白天每公里价格(元)','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','price_per_km_daytime';
# EXEC sys.sp_addextendedproperty 'MS_Description','夜间每公里价格(元)','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','price_per_km_nighttime';
# EXEC sys.sp_addextendedproperty 'MS_Description','夜间开始时间(24小时制)','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','night_hour';
# EXEC sys.sp_addextendedproperty 'MS_Description','城市名称','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','city';
# EXEC sys.sp_addextendedproperty 'MS_Description','创建时间','SCHEMA','dbo','TABLE','t_travel_cost_base','COLUMN','create_time';
