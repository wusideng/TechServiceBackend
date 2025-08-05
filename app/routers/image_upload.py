from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.dependencies import get_sys_token_header
from app.lib.utils.upload import upload_file_to_cdn, delete_file_from_cdn
from config import server_port

router = APIRouter(
    prefix="/image_upload",
    tags=["image_upload"],
)


@router.post("/upload")
async def upload_image(file: UploadFile, upload_cdn_folder_path: str):
    """
    上传图片到CDN
    :param file: 上传的图片文件
    :param folder: CDN上的文件夹路径，默认为'images'
    :return: 图片的CDN访问URL
    """
    try:
        # 生成唯一文件名

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # 上传到CDN
        photo_filename = f"{server_port}{file.filename}{timestamp}"

        image_url = await upload_file_to_cdn(
            file, upload_cdn_folder_path, photo_filename, use_cdn_path=False
        )
        return image_url
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_image(image_path: str):
    """
    从CDN删除图片
    :param image_path: 图片在CDN上的路径(不包含static_url前缀)
    :return: 删除操作结果
    """
    try:
        success = await delete_file_from_cdn(image_path)
        if success:
            return {"message": "Image deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
