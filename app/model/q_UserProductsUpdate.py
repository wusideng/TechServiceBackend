from typing import List
from sqlmodel import SQLModel


class UserProductsUpdate(SQLModel):
    product_ids: List[int]  # 需要更新的产品 ID 列表
