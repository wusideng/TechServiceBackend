import http.client
import base64
import time
import hashlib
import json
from fastapi import APIRouter, HTTPException
from sqlmodel import SQLModel, Session, select
from app.core.database import engine
from config import app_id, app_secret

from app.model.t_order import T_Order
from app.model.t_tech_user import T_Tech_User
from app.model.t_client_user import T_Client_User
from logger import logger

appId = "450609"
token = "a790377c14c7412fa510e2e59a5ec7e9"
# middleNumber = "02160781570"  # 小号号码
# middleNumber = "19961318481"  # 云信提供过度方案：小号号码（重庆）
middleNumber = "02552451865"  # 云信提供过度方案：小号号码（南京）
bindNumberA = ""  # 绑定小号的号码A
bindNumberB = ""  # 绑定小号的号码B
maxBindingTime = 10800  # null 绑定关系有效时长 (秒) 3小时
maxCallDuration = 300  # null 最大通话时长 (秒) 5分钟
callbackUrl = ""  # null 呼叫结果推送地址，http协议
areaCode = ""  # null 不指定小号时，系统根据区号绑定小号资源(使用该功能需要申请报备)
customerData = ""  # null 系统接收用户用户定义数据，自定义数据会随话单回执一起推送
isDeleteTransfer = 1  # 是否删除转移关系,删除时需要提供中间号和之前设置的转移号码

# 绑定电话
# url_bind = "https://101.37.133.245:11008/voice/1.0.0/middleNumberAXB"
# url_bind = "http://101.37.133.245:11108/voice/1.0.0/middleNumberAXB"
host_url_virtual = "101.37.133.245"  # 只使用主机名，不包括协议
port_url_virtual = 11108  # 确保端口号正确
uri_bind_virtual = "/voice/1.0.0/middleNumberAXB"
# 取消绑定
url_unbind = "https://101.37.133.245:11008/voice/1.0.0/middleNumberUnbind/{appID}/{sig}"
uri_unbind_virtual = "/voice/1.0.0/middleNumberUnbind"

# 云信留客（云信小号）
# 虚拟电话拨打
router = APIRouter(
    prefix="/VirtualTelYxlk",
    tags=["VirtualTelYxlk"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


# 云信留客，虚拟拨号，绑定AXB通话
# from 18614032685
# to 18010260892
# to 13683575261 姜
# to 13452762588/18996531158 蒋
# to 蒋娜 19132187173
@router.post("/bind")
async def bind_phone(fromNumber: str, toNumber: str):
    timestamp = str(int(time.time() * 1000))  # 获取当前时间戳，单位为毫秒
    data = f"{appId}:{timestamp}"
    authorization = base64.b64encode(data.encode("utf-8")).decode("utf-8")
    headers = {
        "Content-type": "application/json; charset=utf-8",
        "Authorization": authorization,
    }

    def get_md5(data):
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    sig = get_md5(appId + token + timestamp)
    # 生成最终接口访问地址
    final_uri = f"{uri_bind_virtual}/{appId}/{sig}"
    request_body = {
        "appId": appId,
        "token": token,
        "middleNumber": middleNumber,
        "bindNumberA": fromNumber,
        "bindNumberB": toNumber,
        "maxBindingTime": maxBindingTime,
        "maxCallDuration": maxCallDuration,
    }
    conn = http.client.HTTPConnection(
        host_url_virtual, port=port_url_virtual, timeout=30
    )
    try:
        json_body = json.dumps(request_body)  # 尝试将请求体转换为 JSON 字符串
    except (TypeError, ValueError) as e:
        logger.info("Error: The request body is not a valid JSON format.")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    conn.request("POST", final_uri, json_body, headers)
    response = conn.getresponse()
    response_str = response.read()
    logger.info("Response Status Code:", response.status)
    logger.info("Response Body:", response_str.decode("utf-8"))
    conn.close()
    return response_str

# 云信留客，虚拟拨号，解绑AXB通话
@router.post("/unBind")
async def unbind_phone(fromNumber: str, toNumber: str):
    timestamp = str(int(time.time() * 1000))  # 获取当前时间戳，单位为毫秒
    data = f"{appId}:{timestamp}"
    authorization = base64.b64encode(data.encode("utf-8")).decode("utf-8")
    headers = {
        "Content-type": "application/json; charset=utf-8",
        "Authorization": authorization,
    }

    def get_md5(data):
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    sig = get_md5(appId + token + timestamp)
    # 生成最终接口访问地址
    final_uri = f"{uri_unbind_virtual}/{appId}/{sig}"
    request_body = {
        "appId": appId,
        "token": token,
        "middleNumber": middleNumber,
        "bindNumberA": fromNumber,
        "bindNumberB": toNumber,
    }
    conn = http.client.HTTPConnection(
        host_url_virtual, port=port_url_virtual, timeout=30
    )
    try:
        json_body = json.dumps(request_body)  # 尝试将请求体转换为 JSON 字符串
    except (TypeError, ValueError) as e:
        logger.info("Error: The request body is not a valid JSON format.")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    conn.request("POST", final_uri, json_body, headers)
    response = conn.getresponse()
    response_str = response.read()
    logger.info("Response Status Code:", response.status)
    logger.info("Response Body:", response_str.decode("utf-8"))
    conn.close()
    return response_str


# 订单通知 AXB方式绑定顾客和技师电话号码
# t_client_user.user_phone, t_tech_user.work_phone, 城市管理员，超级管理员
# eg: 195 tech_user_id BeijingMocka 18010260892  client_user_id oK9p06eiEk0jWNvowVjb5lGlkocM 18614032685
@router.post("/bindByOrder")
async def bind_phone_by_order(order_id: str):
    with Session(engine) as session:
        statement = session.exec(
            select(T_Order, T_Tech_User, T_Client_User)  # 在select中添加T_Client_User
            .join(T_Tech_User, T_Order.tech_user_id == T_Tech_User.openid)
            .join(
                T_Client_User, T_Order.client_user_id == T_Client_User.openid
            )  # 添加对T_Client_User的关联
            .where(T_Order.order_id == order_id)
        ).first()
        if not statement:
            raise HTTPException(status_code=404, detail="Order not found")
        tech_user = statement.T_Tech_User
        client_user = statement.T_Client_User
        res = await bind_phone(tech_user.work_phone, client_user.user_phone)
        logger.info(f"bind phone by order {res}")
        return {"from": tech_user.work_phone, "to": client_user.user_phone, "res": res}
    return

# 订单通知 AXB方式解绑顾客和技师电话号码 
@router.post("/unbindByOrder")
async def unbind_phone_by_order(order_id: str):
    with Session(engine) as session:
        statement = session.exec(
            select(T_Order, T_Tech_User, T_Client_User)  # 在select中添加T_Client_User
            .join(T_Tech_User, T_Order.tech_user_id == T_Tech_User.openid)
            .join(
                T_Client_User, T_Order.client_user_id == T_Client_User.openid
            )  # 添加对T_Client_User的关联
            .where(T_Order.order_id == order_id)
        ).first()
        if not statement:
            raise HTTPException(status_code=404, detail="Order not found")
        tech_user = statement.T_Tech_User
        client_user = statement.T_Client_User
        order = statement.T_Order
        res = await unbind_phone(tech_user.work_phone, client_user.user_phone)
        return {"from": tech_user.work_phone, "to": client_user.user_phone, "res": res}
    return
