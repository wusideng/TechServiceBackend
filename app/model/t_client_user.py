from typing import List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import Optional

from app.model.t_user_follows import T_User_Follows


class T_Client_User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    user_pwd: str
    user_createtime: datetime = Field(default_factory=datetime.now)
    user_phone: Optional[str] = Field(nullable=True)
    headimgurl: str
    user_nickname: str
    user_age: int
    user_sex: str
    user_photo: str
    user_grade: int
    user_city: Optional[str]
    user_location: Optional[str]
    user_be_report: Optional[str]
    user_be_blacklist: Optional[str]
    openid: str
    invite_code: Optional[str]
    orders: List["T_Order"] = Relationship(back_populates="client")
    following_tech_list: List[T_User_Follows] = Relationship()


# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_client_user')

# CREATE TABLE [dbo].[t_client_user](
#   [user_id] INT IDENTITY(1,1) PRIMARY KEY,
#   [user_pwd] nvarchar(20) NOT NULL,
#   [user_phone] nvarchar(20) NOT NULL,
#   [headimgurl] nvarchar(200) NOT NULL,
#   [user_nickname] nvarchar(20) NOT NULL,
#   [user_sex] nvarchar(20) NOT NULL,
#   [user_age] int NOT NULL,
#   [user_photo] nvarchar(200) NOT NULL,
#   [openid] nvarchar(50) NOT NULL,
#   [work_phone] nvarchar(20) NOT NULL,
#   [user_city] nvarchar(20) NOT NULL,
#   [user_location] nvarchar(20) NOT NULL,
#   [user_grade] int NOT NULL,
#   [user_be_report] nvarchar(200) NULL,
#   [user_be_blacklist] nvarchar(200) NULL,
#   ) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','客户ID（主键）','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户密码','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_pwd';
# EXEC sys.sp_addextendedproperty 'MS_Description','手机号码','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_phone';
# EXEC sys.sp_addextendedproperty 'MS_Description','微信头像','SCHEMA','dbo','TABLE','t_client_user','COLUMN','headimgurl';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户昵称','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_nickname';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户性别','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_sex';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户年龄','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_age';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户头像','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_photo';
# EXEC sys.sp_addextendedproperty 'MS_Description','微信账号(openid)','SCHEMA','dbo','TABLE','t_client_user','COLUMN','openid';
# EXEC sys.sp_addextendedproperty 'MS_Description','工作电话（接单号码）','SCHEMA','dbo','TABLE','t_client_user','COLUMN','work_phone';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户所在城市','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_city';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户位置','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_location';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户等级','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_grade';
# EXEC sys.sp_addextendedproperty 'MS_Description','是否被投诉','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_be_report';
# EXEC sys.sp_addextendedproperty 'MS_Description','是否被拉黑','SCHEMA','dbo','TABLE','t_client_user','COLUMN','user_be_blacklist';
