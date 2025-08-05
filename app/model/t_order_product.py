from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional


class T_Order_Product(SQLModel, table=True):
  order_p_id: Optional[int] = Field(default=None, primary_key=True)
  product_id: int = Field(foreign_key="t_product.product_id")
  order_id: int = Field(foreign_key="t_order.order_id")
  product_name: str
  product_count: int
  price_current: Decimal
  duration: Optional[str]
  body_parts: Optional[str]
  photo_intro: Optional[str]
  order_time: datetime = Field(default_factory=datetime.now)
  server_time: datetime 
  order: Optional["T_Order"] = Relationship(back_populates="order_products")


# CREATE TABLE [dbo].[t_order_product](	
# 	[order_p_id] INT IDENTITY(1,1) PRIMARY KEY,	
# 	[product_id] nvarchar(20) NOT NULL,	
# 	[order_id] nvarchar(20) NOT NULL,	
# 	[product_name] nvarchar(20) NOT NULL,	
# 	[price_current] decimal NOT NULL,	
# 	[duration] nvarchar(20) NOT NULL,	
# 	[body_parts] nvarchar(500) NULL,	
# 	[photo_intro] nvarchar(500) NULL,
# 	[product_count] int NOT NULL,	
# 	[order_time] datetime NOT NULL,	
# 	[server_time] datetime NOT NULL,	
# ) ON [PRIMARY]


# EXEC sys.sp_addextendedproperty 'MS_Description','主键订单ID','SCHEMA','dbo','TABLE','t_order_product','COLUMN','order_p_id'; 
# EXEC sys.sp_addextendedproperty 'MS_Description','产品id','SCHEMA','dbo','TABLE','t_order_product','COLUMN','product_id'; 
# EXEC sys.sp_addextendedproperty 'MS_Description','订单id','SCHEMA','dbo','TABLE','t_order_product','COLUMN','order_id'; 
# EXEC sys.sp_addextendedproperty 'MS_Description','产品名称','SCHEMA','dbo','TABLE','t_order_product','COLUMN','product_name'; 
# EXEC sys.sp_addextendedproperty 'MS_Description','产品价格','SCHEMA','dbo','TABLE','t_order_product','COLUMN','price_current'; 
# EXEC sys.sp_addextendedproperty 'MS_Description','产品数量','SCHEMA','dbo','TABLE','t_order_product','COLUMN','product_count'; 
# EXEC sys.sp_addextendedproperty 'MS_Description','订单时间','SCHEMA','dbo','TABLE','t_order_product','COLUMN','order_time'; 
# EXEC sys.sp_addextendedproperty 'MS_Description','服务开始时间','SCHEMA','dbo','TABLE','t_order_product','COLUMN','server_time'; 