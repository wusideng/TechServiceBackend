from fastapi import APIRouter, HTTPException, Request
from starlette.responses import StreamingResponse
from datetime import datetime, timedelta
import secrets

from app.lib.utils.captcha import (
    generate_captcha_image_from_text,
    generate_captcha_text,
)
from app.model.q_CaptchaVerify import CaptchaVerifyRequest

router = APIRouter(
    prefix="/tech_certify",
)


@router.get("/captcha")
async def get_captcha(request: Request, width: int = 160, height: int = 40):
    captcha_text = generate_captcha_text()
    img_data = generate_captcha_image_from_text(captcha_text, width, height)
    # 生成唯一ID
    captcha_id = secrets.token_urlsafe(16)
    # 存储到会话中，包含验证码和过期时间
    request.session[f"captcha_{captcha_id}"] = {
        "text": captcha_text,
        "expires": (datetime.now() + timedelta(seconds=30)).timestamp(),
        "attempts": 0,  # 记录尝试次数
    }

    # 设置响应头
    response = StreamingResponse(img_data, media_type="image/png")
    response.set_cookie(
        key="captcha_id",
        value=captcha_id,
        httponly=True,
        max_age=300,
        samesite="strict",
    )

    return response


@router.post("/verify_captcha")
async def verify_captcha(request: Request, info: CaptchaVerifyRequest):
    captcha_input = info.captcha_text
    # 获取验证码ID
    captcha_id = request.cookies.get("captcha_id")
    if not captcha_id:
        raise HTTPException(status_code=400, detail="验证码会话无效")

    # 获取存储的验证码信息
    captcha_key = f"captcha_{captcha_id}"
    captcha_data = request.session.get(captcha_key)

    if not captcha_data:
        raise HTTPException(status_code=400, detail="验证码已过期")

    # 检查是否过期
    if datetime.now().timestamp() > captcha_data["expires"]:
        del request.session[captcha_key]
        raise HTTPException(status_code=400, detail="验证码已过期")

    # 增加尝试次数
    captcha_data["attempts"] += 1
    request.session[captcha_key] = captcha_data

    # 检查尝试次数是否过多（防暴力破解）
    if captcha_data["attempts"] > 3:
        del request.session[captcha_key]
        raise HTTPException(status_code=400, detail="尝试次数过多，请重新获取验证码")

    # 验证码比较（不区分大小写）
    if captcha_input.lower() != captcha_data["text"].lower():
        raise HTTPException(status_code=400, detail="验证码错误")

    # 验证通过，清除验证码
    del request.session[captcha_key]
    response = {"status": "success", "message": "验证成功"}

    return response
