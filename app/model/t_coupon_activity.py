from datetime import datetime
import json
from sqlmodel import Field, Relationship, SQLModel
from typing import Any, List, Optional


class T_Coupon_Activity(SQLModel, table=True):
    __tablename__ = "t_coupon_activity"

    activity_id: Optional[int] = Field(default=None, primary_key=True)
    activity_name: str
    start_time: datetime
    end_time: datetime
    img_url: str
    activity_status: str
    create_time: datetime = Field(default_factory=datetime.now)
    coupons: str = Field(default="[]")  # JSON 字符串

    # 辅助方法
    def get_coupons(self) -> List[Any]:
        """获取优惠券列表"""
        return json.loads(self.coupons) if self.coupons else []

    def set_coupons(self, coupon_list: List[Any]):
        """设置优惠券列表"""
        self.coupons = json.dumps(coupon_list, ensure_ascii=False)


# example of coupons: [{"amount":1,"coupon_value":25,"coupon_condition":245},{"amount":3,"coupon_value":10,"coupon_condition":0}]
