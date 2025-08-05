import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.routers import (
    virtual_tel_yxlk,
    voice_sms_hywx,
    wx_user,
    sys_user,
    products,
    orders,
    orders_tech,
    order_pay,
    order_refund,
    order_product,
    order_status,
    order_comment,
    order_alarm,
    bill,
    feedback,
    coupon,
    tech_user,
    tech_user_contract,
    tech_user_joinus,
    tech_user_auth,
    tech_user_mock,
    tech_user_worktime,
    # tech_user_position,
    tech_user_product,
    tech_user_contract,
    tech_certify,
    tech_address,
    travel_cost,
    apply_status,
    client_user,
    client_user_position,
    user_address,
    user_follow,
    wx_notify,
    recruit,
    city,
    coupon_activity,
    image_upload,
)

# CORS 配置
origins = [
    "http://localhost:8000",  # 允许的前端地址（根据你的前端实际端口）
    "http://127.0.0.1:8000",
    "http://localhost:8001",  # 允许的前端地址（根据你的前端实际端口）
    "http://127.0.0.1:8001",
    "http://visualstreet.cn",
    "http://visualstreet.cn:8000",
    "https://localhost:8000",  # 允许的前端地址（根据你的前端实际端口）
    "https://127.0.0.1:8000",
    "https://localhost:8001",  # 允许的前端地址（根据你的前端实际端口）
    "https://127.0.0.1:8001",
    "https://visualstreet.cn",
    "https://visualstreet.cn:8000",
    "https://visualstreet.cn:8001",
    # 其他允许的地址...
]

UPLOAD_DIR = "uploads"
CDN_DIR = "cdn"


def create_app() -> FastAPI:
    app = FastAPI()

    # 设置静态文件目录
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    # 设置静态文件目录
    app.mount("/cdn", StaticFiles(directory=CDN_DIR), name="cdn")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # 设置允许的源
        allow_credentials=True,
        allow_methods=["*"],  # 允许的方法（GET, POST等）
        allow_headers=["*"],  # 允许的请求头
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=secrets.token_urlsafe(32),
        max_age=30,  # 会话有效期5分钟
    )

    @app.get("/")
    async def root():
        return {"message": "Hello Bigger Applications!"}

    # 微信登陆
    app.include_router(wx_user.router)
    # 语音通信
    app.include_router(voice_sms_hywx.router)
    # 虚拟拨号
    app.include_router(virtual_tel_yxlk.router)
    # 平台端
    app.include_router(sys_user.router)
    app.include_router(products.router)
    app.include_router(orders.router)
    app.include_router(order_product.router)
    app.include_router(order_pay.router)
    app.include_router(order_refund.router)
    app.include_router(order_status.router)
    app.include_router(order_comment.router)
    app.include_router(order_alarm.router)
    app.include_router(bill.router)
    app.include_router(coupon.router)
    app.include_router(feedback.router)
    app.include_router(image_upload.router)
    app.include_router(coupon_activity.router)
    app.include_router(travel_cost.router)

    # 技师端
    app.include_router(tech_user.router)
    app.include_router(tech_user_joinus.router)
    app.include_router(tech_user_auth.router)
    app.include_router(tech_user_mock.router)
    app.include_router(tech_user_worktime.router)
    # app.include_router(tech_user_position.router)
    app.include_router(tech_user_product.router)
    app.include_router(orders_tech.router)
    app.include_router(apply_status.router)
    app.include_router(tech_user_contract.router)
    app.include_router(tech_address.router)

    # 客户端
    app.include_router(client_user.router)
    app.include_router(client_user_position.router)
    app.include_router(user_address.router)
    app.include_router(user_follow.router)
    app.include_router(tech_certify.router)

    # 微信通知
    app.include_router(wx_notify.router)
    # 城市代理/技师招募
    app.include_router(recruit.router)
    app.include_router(city.router)

    return app


app = create_app()
