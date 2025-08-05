from typing import Dict
import json
from pydantic import BaseModel
from config import (
    product_base,
    product_pictures,
    order_pictures,
    app_id,
    mch_id,
    device_info,
    weixin_pay,
    db_name,
    key,
)


class Settings(BaseModel):
    PRODUCT_BASE: str = product_base
    PRODUCT_PICTURES: str = product_pictures
    ORDER_PICTURES: str = order_pictures
    APPID: str = app_id
    MCHID: str = mch_id
    DEVICEINFO: str = device_info
    WEIXIN_PAY: str = weixin_pay
    KEY: str = key
    CDN_PATH: str = "dev" if db_name.endswith("dev") else "prod"


settings = Settings()
# settings = SettingsDev()


# 1704709597	北京尚阳雕漆文化有限公司	尚达元	普通商户	查看
# 行业类目：餐饮、零售批发、网上综合商城、交通出行、生活娱乐服务、培训教育机构、民营医疗机构、缴费等
# 2025/01/18~2025/09/30 非信用卡0.54%、信用卡0.54%，2025/10/01~长期 非信用卡0.6%、信用卡0.6%

# 1704788658	北京尚阳雕漆文化有限公司	尚达元到家服务	普通商户	查看
action_status_code_dict: Dict[str, Dict[str, Dict[str, str]]] = None
with open("app/lib/action_status_code_dict.json", "r", encoding="utf-8") as f:
    action_status_code_dict = json.load(f)
