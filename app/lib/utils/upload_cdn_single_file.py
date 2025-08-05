from fastapi import UploadFile
from qiniu import Auth, put_data, BucketManager
from io import BytesIO
from config import cdn_info
import asyncio
from functools import partial
from logger import logger


access_key = cdn_info["access_key"]
secret_key = cdn_info["secret_key"]
bucket_name = cdn_info["bucket"]


async def upload_single_file_to_qiniu(upload_file: UploadFile, file_key=None):
    # 初始化Auth对象
    q = Auth(access_key, secret_key)

    # 如果没有指定文件名，使用上传文件的文件名
    if not file_key:
        file_key = upload_file.filename

    # 生成上传凭证
    token = q.upload_token(bucket_name, file_key, 3600)

    # 读取文件内容
    file_data = await upload_file.read()

    # 定义同步上传函数
    def _sync_upload(token, key, data):
        return put_data(token, key, data)

    # 在事件循环的默认线程池中异步执行同步上传操作
    loop = asyncio.get_running_loop()
    ret, info = await loop.run_in_executor(
        None, partial(_sync_upload, token, file_key, file_data)
    )

    # 打印上传结果
    logger.info(f"上传状态: {info.status_code}")
    logger.info(f"上传响应: {info}")

    if info.status_code == 200:
        logger.info(f"上传成功! 文件hash: {ret['hash']}")
        return ret, None
    else:
        logger.info(f"上传失败: {info.error}")
        return None, None


async def upload_single_fileio_to_qiniu(
    io_file: BytesIO,
    file_key=None,
    filename="未命名",
):
    # 初始化Auth对象
    q = Auth(access_key, secret_key)

    # 使用上传文件的文件名
    if not file_key:
        file_key = filename

    # 生成上传凭证
    token = q.upload_token(bucket_name, file_key, 3600)

    # 读取文件内容
    file_data = io_file.getvalue()
    io_file.close()

    # 定义同步上传函数
    def _sync_upload(token, key, data):
        return put_data(token, key, data)

    # 在事件循环的默认线程池中异步执行同步上传操作
    loop = asyncio.get_running_loop()
    ret, info = await loop.run_in_executor(
        None, partial(_sync_upload, token, file_key, file_data)
    )

    # 打印上传结果
    print(f"上传状态: {info.status_code}")
    print(f"上传响应: {info}")

    if info.status_code == 200:
        print(f"上传成功! 文件hash: {ret['hash']}")
        return ret, None
    else:
        print(f"上传失败: {info.error}")
        return None, None


async def delete_file_from_qiniu(cdn_path: str) -> bool:
    """
    从CDN删除文件
    :param cdn_path: CDN上的文件路径(不包含static_url前缀)
    :return: 是否删除成功
    """
    try:

        # 初始化Auth状态
        q = Auth(access_key, secret_key)
        # 初始化BucketManager
        bucket = BucketManager(q)
        # 你要测试的空间， 并且这个key在你空间中存在
        key = cdn_path
        # 删除bucket_name 中的文件 key
        ret, info = bucket.delete(bucket_name, key)
        print(info)
        assert ret == {}
        return {"msg": "ok"}
    except Exception as e:
        return {"msg": "failed"}
