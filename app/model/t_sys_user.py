from sqlmodel import Field, SQLModel
from typing import Optional


class T_Sys_User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    user_pwd: str
    user_phone: str
    user_nickname: str
    user_sex: str
    user_age: int
    user_photo: str
    wechat_id: str
    work_phone: str
    user_role: str
    user_city: Optional[str]


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_sys_user')

# CREATE TABLE [dbo].[t_sys_user](
#   [user_id] INT IDENTITY(1,1) PRIMARY KEY,
#   [user_pwd] nvarchar(20) NOT NULL,
#   [user_phone] nvarchar(20) NOT NULL,
#   [user_nickname] nvarchar(20) NOT NULL,
#   [user_sex] nvarchar(20) NOT NULL,
#   [user_age] int NOT NULL,
#   [user_photo] nvarchar(200) NOT NULL,
#   [wechat_id] nvarchar(50) NOT NULL,
#   [work_phone] nvarchar(20) NOT NULL,
#   [user_role] nvarchar(200) NOT NULL,
#   [user_city] nvarchar(200) NULL,
# ) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','管理员ID（主键）','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','管理员密码','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_pwd';
# EXEC sys.sp_addextendedproperty 'MS_Description','手机号码','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_phone';
# EXEC sys.sp_addextendedproperty 'MS_Description','管理员昵称','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_nickname';
# EXEC sys.sp_addextendedproperty 'MS_Description','管理员性别','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_sex';
# EXEC sys.sp_addextendedproperty 'MS_Description','管理员年龄','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_age';
# EXEC sys.sp_addextendedproperty 'MS_Description','管理员头像','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_photo';
# EXEC sys.sp_addextendedproperty 'MS_Description','微信账号','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','wechat_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','工作电话','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','work_phone';
# EXEC sys.sp_addextendedproperty 'MS_Description','管理员角色','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_role';
# EXEC sys.sp_addextendedproperty 'MS_Description','管理城市','SCHEMA','dbo','TABLE','t_sys_user','COLUMN','user_city';
