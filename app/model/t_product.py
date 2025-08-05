from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List


class T_Product(SQLModel, table=True):
    product_id: Optional[int] = Field(default=None, primary_key=True)
    product_name: str
    price_current: int
    price_old: Optional[int] = None
    duration: str
    introduction: Optional[str] = None
    body_parts: Optional[str] = None
    consumables: Optional[str] = None
    contraindication: Optional[str] = None
    promotion: str
    photo_intro: Optional[str] = None
    photo_detail1: Optional[str] = None
    photo_detail2: Optional[str] = None
    photo_detail3: Optional[str] = None

    class Config:
        table_schema = "dbo"  # 指定模式


# EXEC sys.sp_addextendedproperty 'MS_Description','产品id','SCHEMA','dbo','TABLE','t_product','COLUMN','product_id';
# EXEC sys.sp_addextendedproperty 'MS_Description','产品名称','SCHEMA','dbo','TABLE','t_product','COLUMN','product_name';
# EXEC sys.sp_addextendedproperty 'MS_Description','价格','SCHEMA','dbo','TABLE','t_product','COLUMN','price_current';
# EXEC sys.sp_addextendedproperty 'MS_Description','原价','SCHEMA','dbo','TABLE','t_product','COLUMN','price_old';
# EXEC sys.sp_addextendedproperty 'MS_Description','服务时间','SCHEMA','dbo','TABLE','t_product','COLUMN','duration';
# EXEC sys.sp_addextendedproperty 'MS_Description','项目介绍','SCHEMA','dbo','TABLE','t_product','COLUMN','introduction';
# EXEC sys.sp_addextendedproperty 'MS_Description','按摩部位','SCHEMA','dbo','TABLE','t_product','COLUMN','body_parts';
# EXEC sys.sp_addextendedproperty 'MS_Description','耗材（包含物料）','SCHEMA','dbo','TABLE','t_product','COLUMN','consumables';
# EXEC sys.sp_addextendedproperty 'MS_Description','禁忌说明','SCHEMA','dbo','TABLE','t_product','COLUMN','contraindication';
# EXEC sys.sp_addextendedproperty 'MS_Description','推广信息','SCHEMA','dbo','TABLE','t_product','COLUMN','promotion';
# EXEC sys.sp_addextendedproperty 'MS_Description','列表宣传照','SCHEMA','dbo','TABLE','t_product','COLUMN','photo_intro';
# EXEC sys.sp_addextendedproperty 'MS_Description','详细照片1','SCHEMA','dbo','TABLE','t_product','COLUMN','photo_detal1';
# EXEC sys.sp_addextendedproperty 'MS_Description','详细照片2','SCHEMA','dbo','TABLE','t_product','COLUMN','photo_detal2';
# EXEC sys.sp_addextendedproperty 'MS_Description','详细照片3','SCHEMA','dbo','TABLE','t_product','COLUMN','photo_detal3';
