import http.client
import urllib.parse
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import SQLModel, Session, select
from app.core.database import engine

from app.model.t_order import T_Order
from app.model.t_tech_user import T_Tech_User
from app.model.t_client_user import T_Client_User

from config import adminList
from logger import logger

# 互亿无线
# 短息通知，语音通知
router = APIRouter(
    prefix="/hywxVoiceSMS",
    tags=["hywxVoiceSMS"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)

# 语音通知
host_sms_voice = "api.vm.ihuyi.com"
sms_voice_send_uri = "/webservice/voice.php?method=Submit"
account_voice = "VM55207476"
password_voice = "de6db1af479b80707cd1daccd505b6fe"
# 短信通知
host_sms = "106.ihuyi.com"
sms_send_uri = "/webservice/sms.php?method=Submit"
account_sms = "C96134900"
password_sms = "e960da8855e3acdf7511bfdd0d6fc030"


class HYWXReq(SQLModel):
    text: str
    mobile: str


# eg:您的订单号是：0648。已由顺风快递发出，请注意查收。
# 咱们的语音通知话术：
# 1、尚阳科技提醒您，您有一条预约时间为 【6:30】的订单，请注意查看（已申请）
# 2、尚阳科技提醒您，【小小郭】在【北京】有一条预约时间为 【16:30】的订单，请注意查看
# 3、尚阳科技提醒您，【小郭郭】您有一条预约时间为 【16:30】的订单，请注意查看
@router.post("/voice/")
async def send_voice(req: HYWXReq):
    params = urllib.parse.urlencode(
        {
            "account": account_voice,
            "password": password_voice,
            "content": req.text,
            "mobile": req.mobile,
            "format": "json",
        }
    )
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    }
    conn = http.client.HTTPConnection(host_sms_voice, port=80, timeout=30)
    conn.request("POST", sms_voice_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    logger.info(f"send voice response_str {response_str}")
    return response_str


# 您的验证码是：7835。请不要把验证码泄露给其他人。
# 您有一条预约时间为 16:30的订单，请注意查收
# 尚阳科技提醒您，您有一条预约时间为 16:30的订单，请注意查收
# 尊敬的${name}，您的有一条预约时间为 ${time} 的订单，赶快去接单吧。
@router.post("/sms/")
async def send_sms(text: str, mobile: str):
    params = urllib.parse.urlencode(
        {
            "account": account_sms,
            "password": password_sms,
            "content": text,
            "mobile": mobile,
            "format": "json",
        }
    )
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    }
    conn = http.client.HTTPConnection(host_sms, port=80, timeout=30)
    conn.request("POST", sms_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    print(response_str)
    conn.close()
    return response_str


# 订单通知 t_client_user.user_phone, t_tech_user.work_phone, 城市管理员，超级管理员
# 195 tech_user_id BeijingMocka 18010260892  client_user_id oK9p06eiEk0jWNvowVjb5lGlkocM 18614032685
@router.post("/smsorder/")
async def send_voice_order(order_id: str):
    with Session(engine) as session:
        statement = session.exec(
            select(T_Order, T_Tech_User)
            .join(T_Tech_User, T_Order.tech_user_id == T_Tech_User.openid)
            .where(T_Order.order_id == order_id)
        ).first()
        if not statement:
            logger.error("Order not found")
            raise HTTPException(status_code=404, detail="Order not found")

        tech_user = statement.T_Tech_User
        order = statement.T_Order
        logger.info(f"tech_user {tech_user}")
        # logger.info(f"order {order}")
        responseList = []
        # 通知技师
        text = "尚阳科技提醒您，{}您有一条预约时间为 {} 的订单，请注意查看".format(
            tech_user.user_nickname, formatDateToVoice(order.service_time)
        )
        # 语音通知 - 通知技师
        logger.info(tech_user.work_phone)
        logger.info(text)
        voicereq = HYWXReq(text=text, mobile=tech_user.work_phone)
        response = await send_voice(voicereq)
        responseList.append(
            {
                "type": "tech-voice",
                "phone": tech_user.work_phone,
                "text": text,
                "data": response,
            }
        )
        # 短信通知 - 通知技师
        response = await send_sms(text=text, mobile=tech_user.work_phone)
        responseList.append(
            {
                "type": "tech-sms",
                "phone": tech_user.work_phone,
                "text": text,
                "data": response,
            }
        )
        # 通知管理员
        for admin_mobile in adminList:
            admin_text = (
                "尚阳科技提醒您，{}在{}有一条预约时间为 {} 的订单，请注意查看".format(
                    tech_user.user_nickname,
                    order.service_city,
                    formatDateToVoice(order.service_time),
                )
            )
            voicereq = HYWXReq(text=admin_text, mobile=str(admin_mobile))
            # 语音通知 - 通知管理员
            response = await send_voice(voicereq)
            responseList.append(
                {
                    "type": "admin-voice",
                    "phone": admin_mobile,
                    "text": admin_text,
                    "data": response,
                }
            )
            # 短信通知 - 通知管理员
            logger.info(admin_mobile)
            logger.info(admin_text)
            response = await send_sms(text=admin_text, mobile=admin_mobile)
            responseList.append(
                {
                    "type": "admin-sms",
                    "phone": admin_mobile,
                    "text": admin_text,
                    "data": response,
                }
            )
        logger.info(f"responseList {responseList}")
        return responseList


# 假设 formatDateToVoice 是这样一个函数，它接受一个 datetime 对象并返回一个格式化的字符串
def formatDateToVoice(service_time: datetime) -> str:
    return service_time.strftime("%Y年%m月%d日%H点%M分")


@router.post("/smsVerify/")
async def send_sms_tech(phone: str, code: str):
    text = "尚阳科技提醒您，您的验证码是：{}。请不要把验证码泄露给其他人。".format(code)
    response = await send_sms(text=text, mobile=phone)
    return {
        "type": "verify-code",
        "phone": phone,
        "text": text,
        "data": response,
    }
