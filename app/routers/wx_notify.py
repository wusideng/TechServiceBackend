from typing import Dict
from fastapi import APIRouter, Request, Response
import time
import hashlib
import xml.etree.ElementTree as ET

from app.model.t_wechat_event import T_Wechat_Events
from config import WECHAT_TOKEN
from sqlmodel import Session
from app.core.database import engine
from logger import logger

follow_reply = """
欢迎关注 尚达元.上门按摩 全国城市已开放，随时随地按摩放松！

1、点击下方【立即下单】可选择技师及项目在线下单
2、点击下方【我要加入】申请加入尚达元成为一名优秀的手艺人
3、推出五月特惠活动，新人领158元优惠券，享受按摩更优惠。转好友加关注，再领50优惠券

【尚达元】致力于为您提供专业、舒适的按摩服务，助您放松身心、缓解疲劳。
【客服电话】：13452762588
【客服电话】：18010260892
如遇问题请联系客服
"""


# 验证微信签名的函数
def check_signature(signature, timestamp, nonce):
    # 排序
    temp_list = [WECHAT_TOKEN, timestamp, nonce]
    temp_list.sort()

    # 拼接成字符串
    temp_str = "".join(temp_list)

    # SHA1加密
    hash_obj = hashlib.sha1(temp_str.encode("utf-8"))
    calculated_signature = hash_obj.hexdigest()

    # 比较签名
    return calculated_signature == signature


router = APIRouter(
    prefix="/wx_notify",
    tags=["wx_notify"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/wechat")
async def wechat_verify(signature: str, timestamp: str, nonce: str, echostr: str):
    """
    处理微信服务器的验证请求
    """
    # 验证签名
    if check_signature(signature, timestamp, nonce):
        # 验证成功，返回 echostr
        return Response(content=echostr)
    else:
        # 验证失败
        return Response(content="signature fail", status_code=403)


# 处理微信消息和事件的路由
@router.post("/wechat")
async def wechat_message(
    request: Request,
    signature: str = None,
    timestamp: str = None,
    nonce: str = None,
    echostr: str = None,
):
    """
    处理微信服务器推送的消息和事件
    """
    # 验证签名
    if not signature or not timestamp or not nonce:
        return Response(content="missing params", status_code=400)

    if not check_signature(signature, timestamp, nonce):
        return Response(content="signature fail", status_code=403)

    # 获取请求体中的XML
    body = await request.body()
    xml_data = body.decode("utf-8")

    if not xml_data:
        if echostr:
            return Response(content=echostr)
        return Response(content="success")
    #  解析XML
    msg = parse_xml(xml_data)
    if msg.get("MsgType") == "event":
        # 处理事件
        event_type = msg.get("Event", "").lower()
        if event_type == "scan":
            # 已关注用户扫描带参数二维码
            return handle_scan_event(msg)
        elif event_type == "subscribe":
            # 处理关注事件
            if "EventKey" in msg and msg["EventKey"]:
                # 用户扫描带参数二维码进行关注
                # 注意: EventKey会带有前缀"qrscene_"
                return handle_subscribe_with_qr(msg)
            else:
                # 普通关注事件, 应该是用户搜索公众号名称关注的
                return handle_normal_subscribe(msg)
    # 默认回复
    return Response(content="success")


def parse_xml(xml_data):
    """解析微信发来的XML数据"""
    if not xml_data:
        return {}

    try:
        root = ET.fromstring(xml_data)
        msg = {}
        for child in root:
            msg[child.tag] = child.text
        return msg
    except Exception as e:
        print(f"解析XML失败: {e}")
        return {}


def build_text_reply(msg, content):
    """构建文本回复"""
    reply = f"""
    <xml>
        <ToUserName><![CDATA[{msg.get('FromUserName', '')}]]></ToUserName>
        <FromUserName><![CDATA[{msg.get('ToUserName', '')}]]></FromUserName>
        <CreateTime>{int(time.time())}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
    </xml>
    """
    return reply


def handle_normal_subscribe(msg: Dict[str, str]) -> Response:
    # 普通关注事件 (通过搜索公众号名称关注)
    reply_content = follow_reply
    reply_msg = build_text_reply(msg, reply_content)
    open_id = msg.get("FromUserName", "")
    logger.info(f"搜索公众号并关注 {open_id}")
    with Session(engine) as session:
        new_wechat_event = T_Wechat_Events(
            user_openid=open_id,
            event_type="normal_follow",
        )
        session.add(new_wechat_event)
        session.commit()
    return Response(content=reply_msg, media_type="application/xml")


def handle_subscribe_with_qr(msg: Dict[str, str]) -> Response:
    # 扫描后点了关注
    # 获取二维码参数 (去掉"qrscene_"前缀)
    event_key = msg.get("EventKey", "")
    open_id = msg.get("FromUserName", "")
    scene_str = (
        event_key.replace("qrscene_", "")
        if event_key.startswith("qrscene_")
        else event_key
    )
    logger.info(f"扫描带参数二维码并关注事件,openid={open_id} scene_str={scene_str}")
    with Session(engine) as session:
        new_wechat_event = T_Wechat_Events(
            user_openid=open_id,
            event_type="scan_and_follow",
            scene_str=scene_str,
        )
        session.add(new_wechat_event)
        session.commit()
    # 构建回复
    reply_content = follow_reply
    reply_msg = build_text_reply(msg, reply_content)
    return Response(content=reply_msg, media_type="application/xml")


def handle_scan_event(msg: Dict[str, str]) -> Response:
    # 关注后又扫描
    # 获取二维码参数
    scene_str = msg.get("EventKey", "")
    # 记录用户数据和二维码参数
    open_id = msg.get("FromUserName", "")
    logger.info(f"关注后又扫描二维码 open_id={open_id} scene_str={scene_str}")
    with Session(engine) as session:
        new_wechat_event = T_Wechat_Events(
            user_openid=open_id,
            event_type="scan_after_follow",
            scene_str=scene_str,
        )
        session.add(new_wechat_event)
        session.commit()

    # 对事件本身只需返回"success"
    return Response(content="success")
