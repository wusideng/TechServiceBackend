from datetime import time
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Time_Slots(SQLModel, table=True):
    slot_id: Optional[int] = Field(default=None, primary_key=True)
    start_time: time
    end_time: time


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_time_slots')

# CREATE TABLE [dbo].[t_time_slots](
# 	[slot_id] INT IDENTITY(1,1) PRIMARY KEY,
#     [start_time] time NOT NULL,
#     [end_time] time NOT NULL) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','时间段id','SCHEMA','dbo','TABLE','t_time_slots','COLUMN','slot_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','开始时间','SCHEMA','dbo','TABLE','t_time_slots','COLUMN','start_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','结束时间','SCHEMA','dbo','TABLE','t_time_slots','COLUMN','end_time';
