from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional


class T_Order_Comment(SQLModel, table=True):
    order_comment_id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="t_order.order_id")
    client_openid: Optional[str]
    client_comment: Optional[str]
    client_comment_time: Optional[datetime]
    client_score_to_tech: Optional[float]
    tech_id: Optional[str] = Field(default=None, foreign_key="t_tech_user.openid")
    tech_comment: Optional[str]
    tech_comment_time: Optional[datetime]
    tech_score_to_client: Optional[float]
    order: Optional["T_Order"] = Relationship(back_populates="order_comment")

    # tech_user: Optional["T_Tech_User"] = Relationship(back_populates="comments")


# CREATE TABLE [dbo].[t_order_comment](
#   [order_comment_id] INT IDENTITY(1,1) PRIMARY KEY,
# 	[order_id] nvarchar(20) NOT NULL,
# 	[client_comment] nvarchar(500) NOT NULL,
# 	[client_comment_time] datetime NOT NULL,
# 	[client_score_to_tech] nvarchar(20) NOT NULL,
# 	[tech_comment] nvarchar(500) NOT NULL,
# 	[tech_comment_time] datetime NOT NULL,
# 	[tech_score_to_client] nvarchar(20) NOT NULL,	) ON [PRIMARY]

# EXEC sys.sp_addextendedproperty 'MS_Description','主键','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','order_comment_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','订单id','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','order_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户评价','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','client_comment';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户评论时间','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','client_comment_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','客户评分','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','client_score_to_tech';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师评价','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','tech_comment';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师评论时间','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','tech_comment_time';
# EXEC sys.sp_addextendedproperty 'MS_Description','技师评分','SCHEMA','dbo','TABLE','t_order_comment','COLUMN','tech_score_to_client';
