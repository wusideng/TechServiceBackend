from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
import httpx
import random
import time
import hashlib

from app.model.t_apply_status import T_Apply_Status
from config import app_id, app_secret
from config import is_dev
from sqlmodel import Session, select
from app.core.database import engine, get_session
from app.model.t_client_user import T_Client_User
from logger import logger
from app.model.t_tech_user import T_Tech_User


is_dev = bool(is_dev) == True

# 替换为您的微信开发者信息
APP_ID = app_id
APP_SECRET = app_secret

router = APIRouter(
    prefix="/wx",
    tags=["wx"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


# 使用 code 获取 access_token
@router.get("/userInfo/{code}")
async def get_userInfo(code: str):
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={APP_ID}&secret={APP_SECRET}&code={code}&grant_type=authorization_code"
            )
            token_data = token_response.json()

            if "errcode" in token_data:
                raise HTTPException(status_code=400, detail=token_data)

            access_token = token_data.get("access_token")
            openid = token_data.get("openid")

            # 使用 access_token 获取用户信息
            user_info_response = await client.get(
                f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN"
            )
            user_info = user_info_response.json()

            if "errcode" in user_info:
                raise HTTPException(status_code=400, detail=user_info)

            return user_info  # 返回用户信息
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user_info/{code}")
async def get_userInfo(
    code: str,
    invite_code: Optional[str] = None,
    session: Session = Depends(get_session),
):
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={APP_ID}&secret={APP_SECRET}&code={code}&grant_type=authorization_code"
            )
            token_data = token_response.json()

            if "errcode" in token_data:
                raise HTTPException(status_code=400, detail=token_data)

            access_token = token_data.get("access_token")
            openid = token_data.get("openid")

            # 使用 access_token 获取用户信息
            user_info_response = await client.get(
                f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN"
            )
            user_info = user_info_response.json()
            # 手机号微信不提供，我们需要让用户设置
            if "errcode" in user_info:
                logger.error(user_info["errorcode"])
                raise HTTPException(status_code=400, detail=user_info)
            # todo
            # 当前因为同源问题（前后端端口不同视为不同源），无法设置cookie，后面需要换node server解决
            # # 设置包含openid的cookie
            # # max_age设置为30天 (60*60*24*30 = 2592000秒)
            # response.set_cookie(
            #     key="openid",
            #     value=openid,
            #     max_age=86400,  # 设置为一天 (24*60*60=86400秒)
            #     path="/devclient/",
            #     domain="visualstreet.cn",
            #     httponly=False,  # 允许JavaScript访问cookie
            #     # secure=True,  # 仅在HTTPS连接中发送
            #     samesite="lax",  # 防止CSRF攻击
            # )
            statement = select(T_Client_User).where(T_Client_User.openid == openid)
            users = session.exec(statement)
            user = users.first()
            if user is None:
                is_new_user = True
                new_user = T_Client_User(
                    user_pwd="string",
                    # user_phone="string",
                    headimgurl=user_info["headimgurl"],
                    user_nickname=user_info["nickname"],
                    user_age=0,
                    user_sex="string",
                    user_photo=user_info["headimgurl"],
                    openid=openid,
                    user_city="string",
                    user_location="string",
                    user_grade=0,
                    user_be_report="string",
                    user_be_blacklist="string",
                    invite_code=invite_code,
                )
                session.add(new_user)
                user = new_user
                need_commit = True
            else:
                need_commit = False
                is_new_user = False
                if user.headimgurl != user_info["headimgurl"]:
                    need_commit = True
                    user.headimgurl = user_info["headimgurl"]
                if user.user_nickname != user_info["nickname"]:
                    need_commit = True
                    user.user_nickname = user_info["nickname"]
                if user.user_photo != user_info["headimgurl"]:
                    need_commit = True
                    user.user_photo = user_info["headimgurl"]
            if need_commit:
                session.commit()
                session.refresh(user)
            result = user.model_dump()
            result["is_new_user"] = is_new_user
            return result

            # return user_info  # 返回用户信息
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tech_user_info/{code}")
async def get_tech_userInfo(
    code: str,
    session: Session = Depends(get_session),
):
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={APP_ID}&secret={APP_SECRET}&code={code}&grant_type=authorization_code"
            )
            token_data = token_response.json()

            if "errcode" in token_data:
                raise HTTPException(status_code=400, detail=token_data)

            access_token = token_data.get("access_token")
            openid = token_data.get("openid")

            # 使用 access_token 获取用户信息
            user_info_response = await client.get(
                f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN"
            )
            user_info = user_info_response.json()
            # 手机号微信不提供，我们需要让用户设置
            if "errcode" in user_info:
                raise HTTPException(status_code=400, detail=user_info)
            # todo
            # 当前因为同源问题（前后端端口不同视为不同源），无法设置cookie，后面需要换node server解决
            # # 设置包含openid的cookie
            # # max_age设置为30天 (60*60*24*30 = 2592000秒)
            # response.set_cookie(
            #     key="openid",
            #     value=openid,
            #     max_age=86400,  # 设置为一天 (24*60*60=86400秒)
            #     path="/devclient/",
            #     domain="visualstreet.cn",
            #     httponly=False,  # 允许JavaScript访问cookie
            #     # secure=True,  # 仅在HTTPS连接中发送
            #     samesite="lax",  # 防止CSRF攻击
            # )
            statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
            users = session.exec(statement)
            user = users.first()
            join_status_statement = (
                select(T_Apply_Status)
                .where(
                    T_Apply_Status.tech_id == openid,
                    T_Apply_Status.apply_type == "tech_join",
                )
                .order_by(T_Apply_Status.createTime.desc())
            )
            join_status = session.exec(join_status_statement).first()

            if user is None:
                is_new_user = True
                new_user = T_Tech_User(
                    headimgurl=user_info["headimgurl"],
                    user_nickname=user_info["nickname"],
                    openid=openid,
                )
                session.add(new_user)
                user = new_user
                need_commit = True
            else:
                need_commit = False
                is_new_user = False
            if need_commit:
                session.commit()
                session.refresh(user)
            result = user.model_dump()
            result["joinStatus"] = (
                join_status.apply_status if join_status else "unapplied"
            )
            result["is_new_user"] = is_new_user
            return result

            # return user_info  # 返回用户信息
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))


# 使用 code 获取 access_token
@router.get("/userInfo/{code}")
async def get_userInfo(code: str):
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={APP_ID}&secret={APP_SECRET}&code={code}&grant_type=authorization_code"
            )
            token_data = token_response.json()

            if "errcode" in token_data:
                raise HTTPException(status_code=400, detail=token_data)

            access_token = token_data.get("access_token")
            openid = token_data.get("openid")

            # 使用 access_token 获取用户信息
            user_info_response = await client.get(
                f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN"
            )
            user_info = user_info_response.json()

            if "errcode" in user_info:
                raise HTTPException(status_code=400, detail=user_info)

            return user_info  # 返回用户信息
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 获取 access_token
@router.get("/get_jsapi_ticket")
async def get_jsapi_ticket(url: str):
    try:
        async with httpx.AsyncClient() as client:
            # can not get result when running locally because local ip not in whitelist
            token_response = await client.get(
                f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
            )
            access_token = token_response.json().get("access_token")
            # 获取 jsapi_ticket
            ticket_response = await client.get(
                f"https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={access_token}&type=jsapi"
            )
            jsapi_ticket = ticket_response.json().get("ticket")

            # 生成签名
            timestamp = int(time.time())
            nonce_str = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16)
            )
            string_to_sign = f"jsapi_ticket={jsapi_ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url}"
            signature = hashlib.sha1(string_to_sign.encode("utf-8")).hexdigest()
            return {
                "appId": APP_ID,
                "timestamp": timestamp,
                "nonceStr": nonce_str,
                "string_to_sign": string_to_sign,
                "signature": signature,
                "access_token": access_token,
                "jsapi_ticket": jsapi_ticket,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 生成邀请码
def generate_code(phone_number):
    # 使用 MD5 哈希算法
    hash_object = hashlib.md5(phone_number.encode())
    # 获取十六进制表示
    hex_dig = hash_object.hexdigest()
    # 返回前16位
    return hex_dig[:16]


# 制作带有参数（invite_code）的二维码
# {
#   "scene": "invite_code=value", // 保存推荐人手机号码作为推广码
#   "page": "pages/index/index", // 页面路径
#   "width": 430
# }
@router.post("/generate_qr_code")
async def generate_qr_code(access_token, phone):
    url = f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}"
    payload = {
        "scene": f"invite_code={phone}",  # 使用手机号码作为参数
        "page": "pages/index/index",  # 小程序页面路径
        "width": 430,  # 二维码的宽度
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            with open("qr_code.png", "wb") as f:
                f.write(response.content)
            logger.info("二维码已生成并保存为 qr_code.png")
            return response.content
        else:
            logger.info("生成二维码失败:", response.json())
            return {"msg": "生成二维码失败:", "data": response.json()}
