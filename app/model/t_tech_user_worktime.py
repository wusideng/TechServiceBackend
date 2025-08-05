from datetime import datetime, date
from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional

from app.model.t_time_slots import T_Time_Slots


class T_Tech_User_Worktime(SQLModel, table=True):
    work_time_id: Optional[int] = Field(default=None, primary_key=True)
    tech_user_id: str = Field(foreign_key="t_tech_user.openid")
    slot_id: int = Field(foreign_key="t_time_slots.slot_id")
    work_date: date
    active: int
    time_slot: T_Time_Slots = Relationship()


# 衍生类
class WorktimeBlock(SQLModel):
    work_date: datetime
    slot_id: int
    active: bool = True


class CreateWorktimeRequest(SQLModel):
    tech_user_id: str
    worktime_blocks: List[WorktimeBlock]


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_tech_user_worktime')

# CREATE TABLE [dbo].[t_tech_user_worktime](
# 	[work_time_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[tech_user_id] int NOT NULL,
# 	[slot_id] int NOT NULL,
# 	[work_date] datetime NOT NULL,
# 	[active] int NOT NULL) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键（时间块ID）','SCHEMA','dbo','TABLE','t_tech_user_worktime','COLUMN','work_time_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师ID','SCHEMA','dbo','TABLE','t_tech_user_worktime','COLUMN','tech_user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','时间段ID','SCHEMA','dbo','TABLE','t_tech_user_worktime','COLUMN','slot_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','工作日期','SCHEMA','dbo','TABLE','t_tech_user_worktime','COLUMN','work_date';
# EXEC sys.sp_addextendedproperty 'MS_Description','是否正在服务','SCHEMA','dbo','TABLE','t_tech_user_worktime','COLUMN','active';
