from sqlmodel import Field, SQLModel
from typing import Optional


class T_Tech_User_Auth(SQLModel, table=True):
    auth_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    auth_type: str
    openid: str
    access_token: str


# CREATE TABLE [dbo].[t_tech_user_auth](
# 	[auth_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[user_id] INT NOT NULL,
# 	[auth_type] nvarchar(20) NOT NULL,
# 	[openid] nvarchar(100) NOT NULL,
# 	[access_token] nvarchar(100) NOT NULL	) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键id','SCHEMA','dbo','TABLE','t_tech_user_auth','COLUMN','auth_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','用户id','SCHEMA','dbo','TABLE','t_tech_user_auth','COLUMN','user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','第三方登录类型（微信/账号密码）','SCHEMA','dbo','TABLE','t_tech_user_auth','COLUMN','auth_type';
# EXEC sys.sp_addextendedproperty 'MS_Description','微信返回的唯一标识','SCHEMA','dbo','TABLE','t_tech_user_auth','COLUMN','openid';
# EXEC sys.sp_addextendedproperty 'MS_Description','微信返回的token','SCHEMA','dbo','TABLE','t_tech_user_auth','COLUMN','access_token';
