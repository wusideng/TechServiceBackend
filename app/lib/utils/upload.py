from fastapi import UploadFile, HTTPException
import os
from app.core.util import settings
from app.lib.utils.upload_cdn_single_file import (
    upload_single_file_to_qiniu,
    upload_single_fileio_to_qiniu,
    delete_file_from_qiniu,
)
from config import static_url
from typing import Union
from fastapi import UploadFile
from io import BytesIO


async def upload_file_to_cdn(
    file: UploadFile,
    upload_cdn_folder_path: str,
    file_name: str,
    use_cdn_path: bool = True,
) -> str:
    """
    上传文件到CDN
    :param file: 上传的文件对象
    :param upload_cdn_folder_path: CDN上的文件夹路径
    :param file_name: 文件名
    :return: 完整的CDN访问URL
    """
    try:
        if use_cdn_path:
            cdn_path = f"{settings.CDN_PATH}/{upload_cdn_folder_path}/{file_name}"
        else:
            cdn_path = f"{upload_cdn_folder_path}/{file_name}"
        await upload_single_file_to_qiniu(file, cdn_path)
        full_cdn_path = f"{static_url}/{cdn_path}"
        return full_cdn_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


async def upload_file_to_local(file: UploadFile, filepath: str, filename: str):
    photo_path = os.path.join(filepath, filename)
    print("photo_path:", photo_path)
    with open(photo_path, "wb") as buffer:
        buffer.write(await file.read())
    return photo_path


async def upload_bytesio_to_cdn(
    file: BytesIO, upload_cdn_folder_path: str, file_name: str
):
    file_data = file
    cdn_path = f"{settings.CDN_PATH}/{upload_cdn_folder_path}/{file_name}"
    await upload_single_fileio_to_qiniu(
        file_data, cdn_path, file_name
    )  # 假设 upload_single_file_to_qiniu 接受 BytesIO
    full_cdn_path = f"{static_url}/{cdn_path}"
    return full_cdn_path


async def delete_file_from_cdn(file_path: str):
    try:
        file_path = file_path.replace(f"{static_url}/", "")
        res = await delete_file_from_qiniu(file_path)
        msg = res["msg"]
        if msg == "ok":
            # return http status 200
            return {"message": "文件删除成功"}
        else:
            raise HTTPException(status_code=500, detail=f"删除文件失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
