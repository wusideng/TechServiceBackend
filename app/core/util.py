import random
import hashlib
import asyncio
from functools import wraps
import string
from typing import Callable, Any, Union
import xmltodict
import httpx
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from hashlib import md5
from datetime import datetime, timedelta


from app.core.config import settings
from config import wx_cert_path, wx_key_path
from logger import logger


def generate_nonce_str(length=32):
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=length))


def generate_signature(params):
    sorted_keys = sorted(params.keys())
    stringA = "&".join(f"{key}={params[key]}" for key in sorted_keys)
    stringSignTemp = f"{stringA}&key={settings.KEY}"
    return hashlib.md5(stringSignTemp.encode("utf-8")).hexdigest().upper()


def retry_request(retry_times: int = 3, interval: float = 1.0):
    """
    装饰器，用于重试超时请求。

    :param retry_times: 最大重试次数，默认为 3。
    :param interval: 每次重试之间的间隔时间（秒），默认为 1.0 秒。
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(retry_times):
                try:
                    # 尝试执行被装饰的请求函数
                    return await func(*args, **kwargs)
                except asyncio.TimeoutError as e:
                    logger.info(f"请求超时: {e}. 第 {attempt + 1} 次重试。")

                # 等待指定的间隔时间再重试
                if attempt < retry_times - 1:
                    await asyncio.sleep(interval)
            # 如果所有重试失败，抛出最后一个异常
            raise Exception(f"请求失败，已重试 {retry_times} 次。")

        return wrapper

    return decorator


@retry_request(retry_times=3, interval=3.0)
async def send_async_request(url: str, data: dict):
    """
    发送带有 XML 数据的 POST 请求。

    :param url: 请求的目标 URL。
    :param data: 请求的 XML 数据（字典形式）。
    :return: 请求的响应对象。
    """
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            data=xmltodict.unparse({"xml": data}),
            headers={"Content-Type": "text/xml"},
            timeout=15,  # 设置超时时间
        )
        # response.raise_for_status()  # 如果响应不是 2xx，则抛出异常
        return response


@retry_request(retry_times=3, interval=3.0)
async def send_async_request_json(url: str, data: dict) -> httpx.Response:
    """
    发送带有 XML 数据的 POST 请求。

    :param url: 请求的目标 URL。
    :param data: 请求的 XML 数据（字典形式）。
    :return: 请求的响应对象。
    """
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            headers={"Content-Type": "application/json"},
            timeout=15,  # 设置超时时间
        )
        # response.raise_for_status()  # 如果响应不是 2xx，则抛出异常
        return response


# def decrypt(nonce, ciphertext, associated_data):
#     key = "Your32Apiv3Key"
#     key_bytes = str.encode(key)
#     nonce_bytes = str.encode(nonce)
#     ad_bytes = str.encode(associated_data)
#     data = base64.b64decode(ciphertext)
#     aesgcm = AESGCM(key_bytes)
#     return aesgcm.decrypt(nonce_bytes, data, ad_bytes)


@retry_request(retry_times=3, interval=3.0)
async def send_async_request_with_cert(url: str, data: dict) -> httpx.Response:
    """
    发送带有 XML 数据的 POST 请求。

    :param url: 请求的目标 URL。
    :param data: 请求的 XML 数据（字典形式）。
    :return: 请求的响应对象。
    """
    async with httpx.AsyncClient(
        timeout=15, cert=(wx_cert_path, wx_key_path)
    ) as client:
        response = await client.post(
            url,
            data=xmltodict.unparse({"xml": data}),
            headers={"Content-Type": "text/xml"},
            timeout=15,  # 设置超时时间
        )
        # response.raise_for_status()  # 如果响应不是 2xx，则抛出异常
        return response


def get_md5(text):
    md5_obj = hashlib.md5()
    md5_obj.update(text.encode("utf-8"))
    return md5_obj.hexdigest()


def decrypt_req_info(req_info: str, api_key: str) -> dict:
    try:
        # MD5处理key
        key = get_md5(api_key)

        # Base64解码
        bs_data = base64.b64decode(req_info.encode("utf-8"))

        # 初始化AES解密器
        cipher = Cipher(
            algorithms.AES(key.encode("utf-8")), modes.ECB(), backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # 解密
        decrypted_bytes = decryptor.update(bs_data) + decryptor.finalize()
        decrypted_text = decrypted_bytes.decode("utf-8")

        # 去除PKCS7补位
        new_data = decrypted_text[: -ord(decrypted_text[-1])]

        # XML转dict
        data_dict = xmltodict.parse(new_data).get("root")

        return data_dict

    except Exception as e:
        raise Exception(f"解密失败: {str(e)}")


def get_latest_slot_id() -> Union[int, None]:
    time_obj = get_latest_available_worktime().time()
    # Calculate total minutes since midnight
    total_minutes = time_obj.hour * 60 + time_obj.minute

    # Calculate which 30-minute slot this falls into (1-based indexing)
    slot_id = (total_minutes // 30) + 2

    # Handle the edge case of 24:00:00 (which should be slot 48)
    if slot_id > 48:
        slot_id = None
    return slot_id


default_travel_time_for_slot_calculation_minutes = 15


def get_latest_available_worktime():
    time_obj = datetime.now() + timedelta(
        minutes=default_travel_time_for_slot_calculation_minutes
    )
    return time_obj


# 生成6位数字验证码
def generate_sms_code():
    return "".join(random.choices(string.digits, k=6))
