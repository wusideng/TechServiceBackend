import requests
import json
from get_access_token import get_access_token

scene_str = "handwash"


def create_temp_qrcode(expire_days: int = 30):  # 默认30天
    expire_seconds = 3600 * 24 * expire_days
    access_token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={access_token}"

    data = {
        "expire_seconds": expire_seconds,
        "action_name": "QR_STR_SCENE",
        "action_info": {"scene": {"scene_str": scene_str}},
    }

    response = requests.post(url, data=json.dumps(data))
    result = response.json()
    if "ticket" in result:
        print(result)
        ticket = result["ticket"]
        url = f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={ticket}"
        print(url)
    else:
        print(f"创建二维码失败: {result}")
        return None


def create_permanent_qrcode():
    access_token = get_access_token()
    print(access_token)
    url = f"https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={access_token}"

    data = {
        "action_name": "QR_LIMIT_STR_SCENE",
        "action_info": {"scene": {"scene_str": scene_str}},
    }

    response = requests.post(url, data=json.dumps(data))
    result = response.json()

    if "ticket" in result:
        print(result)
        ticket = result["ticket"]
        url = f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={ticket}"
        print(url)
    else:
        print(f"创建二维码失败: {result}")
        return None


if __name__ == "__main__":
    create_permanent_qrcode()
