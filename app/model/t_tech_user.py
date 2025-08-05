from typing import List, Optional
from sqlalchemy import desc
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

from app.model.t_order_comment import T_Order_Comment
from app.model.t_tech_user_product import T_Tech_User_Product


class T_Tech_User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    user_pwd: Optional[str]
    user_createtime: datetime = Field(default_factory=datetime.now)
    user_phone: Optional[str]
    user_nickname: str
    user_sex: Optional[str]
    user_age: Optional[int]
    user_city: Optional[str]
    idnetity_card: Optional[str]
    openid: str
    headimgurl: str
    work_phone: Optional[str]
    bank_card_id: Optional[str]
    bank_card_type: Optional[str]
    user_desc: Optional[str]
    photo_work: Optional[str]
    photo_life_1: Optional[str]
    photo_life_2: Optional[str]
    photo_life_3: Optional[str]
    user_online_status: Optional[str]
    business_license: Optional[str]
    ratio: Optional[int]
    technician_certificate: Optional[str]
    health_certificate: Optional[str]
    orders: List["T_Order"] = Relationship(
        back_populates="tech",
        sa_relationship_kwargs={"foreign_keys": "[T_Order.tech_user_id]"},
    )
    tech_user_products: List[T_Tech_User_Product] = Relationship()
    comments: List["T_Order_Comment"] = Relationship(
        sa_relationship_kwargs={
            "order_by": lambda: desc(T_Order_Comment.client_comment_time)
        },
    )

    # 	[business_license] nvarchar(200) NULL,


#     [technician_certificate] nvarchar(200) NULL,
#     [health_certificate] nvarchar(200) NULL,

# IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='t_tech_user')

# CREATE TABLE [dbo].[t_tech_user](
# 	[uesr_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[user_pwd] [nvarchar](20) NOT NULL,
# 	[user_phone] [nvarchar](20) NOT NULL,
# 	[user_nickname] [nvarchar](20) NOT NULL,
# 	[user_sex] [nvarchar](20) NOT NULL,
# 	[user_age] [int] NOT NULL,
# 	[user_stature] [int] NULL,
# 	[user_weight] [int] NULL,
# 	[user_city] [nvarchar](20) NOT NULL,
# 	[idnetity_card] [nvarchar](20) NOT NULL,
# 	[openid] [nvarchar](100) NOT NULL,
# 	[headimgurl] [nvarchar](200) NOT NULL,
# 	[work_phone] [nvarchar](20) NOT NULL,
# 	[bank_card_id] [nvarchar](2	0) NOT NULL,
# 	[bank_card_type] [nvarchar](20) NOT NULL,
# 	[user_desc] [nvarchar](500) NULL,
# 	[photo_work] [nvarchar](200) NULL,
# 	[photo_life_1] [nvarchar](200) NULL,
# 	[photo_life_2] [nvarchar](200) NULL,
# 	[photo_life_3] [nvarchar](200) NULL,
# 	[business_license] nvarchar(200) NULL,
#     [technician_certificate] nvarchar(200) NULL,
#     [health_certificate] nvarchar(200) NULL,
# 	) ON [PRIMARY]
# GO

# EXEC sys.sp_addextendedproperty 'MS_Description','技师ID（主键）','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师密码','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_pwd';
# EXEC sys.sp_addextendedproperty 'MS_Description','手机号码','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_phone';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师昵称','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_nickname';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师性别','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_sex';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师年龄','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_age';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师身高','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_stature';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师体重','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_weight';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师城市','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_city';
# EXEC sys.sp_addextendedproperty 'MS_Description','身份证号','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','idnetity_card';
# EXEC sys.sp_addextendedproperty 'MS_Description','微信账号','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','openid';
# EXEC sys.sp_addextendedproperty 'MS_Description','微信头像','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','headimgurl';
# EXEC sys.sp_addextendedproperty 'MS_Description','工作电话（接单号码）','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','work_phone';
# EXEC sys.sp_addextendedproperty 'MS_Description','银行卡号','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','bank_card_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','银行卡类型','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','bank_card_type';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师详情','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','user_desc';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师工作照','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','photo_work';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师生活照','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','photo_life_1';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师生活照','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','photo_life_2';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师生活照','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','photo_life_3';
# EXEC sys.sp_addextendedproperty 'MS_Description','商户执照','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','business_license';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师证','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','technician_certificate';
# EXEC sys.sp_addextendedproperty 'MS_Description','健康证','SCHEMA','dbo','TABLE','t_tech_user','COLUMN','health_certificate';
