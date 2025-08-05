from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional

from app.model.t_product import T_Product


class T_Tech_User_Product(SQLModel, table=True):
    user_product_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="t_tech_user.user_id")
    user_nickname: Optional[str] = None
    product_id: int = Field(foreign_key="t_product.product_id")
    product_name: Optional[str] = None
    create_time: datetime = Field(default_factory=datetime.now)
    # # # 与技师的多对一关系
    # tech_user: Optional["T_Tech_User"] = Relationship(
    #     back_populates="tech_user_products"
    # )
    # 与产品的多对一关系
    product: Optional[T_Product] = Relationship()


# CREATE TABLE [dbo].[t_tech_user_product](
#   [user_product_id] INT IDENTITY(1,1) PRIMARY KEY,
#   [user_id] int NOT NULL,
#   [user_nickname] nvarchar(20) NULL,
#   [product_id] int NOT NULL,
#   [product_name] nvarchar(20) NULL,
#   [create_time] datetime NOT NULL
# ) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键id','SCHEMA','dbo','TABLE','t_tech_user_product','COLUMN','user_product_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师id','SCHEMA','dbo','TABLE','t_tech_user_product','COLUMN','user_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师昵称','SCHEMA','dbo','TABLE','t_tech_user_product','COLUMN','user_nickname';
# EXEC sys.sp_addextendedproperty 'MS_Description','产品id','SCHEMA','dbo','TABLE','t_tech_user_product','COLUMN','product_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','产品名称','SCHEMA','dbo','TABLE','t_tech_user_product','COLUMN','product_name';
# EXEC sys.sp_addextendedproperty 'MS_Description','创建时间','SCHEMA','dbo','TABLE','t_tech_user_product','COLUMN','create_time';
