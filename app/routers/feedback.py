import uuid
from typing import Optional
from starlette.responses import Response
from fastapi import APIRouter, File, Form, UploadFile
from sqlmodel import Session, select

from app.core.database import engine
from app.lib.utils.upload import upload_file_to_cdn
from app.model.t_feedback import (
    T_Feedback,
)

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
)


@router.post("/create")
async def create_new_feedback(
    client_openid: str = Form(...),
    content: str = Form(...),
    contact_phone: str = Form(""),
    user_phone_registered: str = Form(""),
    status: int = Form(0),
    image1: Optional[UploadFile] = File(None),
    image2: Optional[UploadFile] = File(None),
    image3: Optional[UploadFile] = File(None),
):
    with Session(engine) as session:
        new_feedback = T_Feedback(
            client_openid=client_openid,
            content=content,
            contact_phone=contact_phone,
            status=status,
            user_phone_registered=user_phone_registered,
        )
        if image1:
            cdn_path = await upload_image_to_cdn(image1)
            new_feedback.img_url1 = cdn_path
        if image2:
            cdn_path = await upload_image_to_cdn(image2)
            new_feedback.img_url2 = cdn_path
        if image3:
            cdn_path = await upload_image_to_cdn(image3)
            new_feedback.img_url3 = cdn_path

        session.add(new_feedback)
        session.commit()
    return Response(status_code=200)


async def upload_image_to_cdn(image: UploadFile):
    random_uuid = uuid.uuid4()
    file_name = f"Feedback_{random_uuid}_{image.filename}"
    upload_folder_path = "uploads"
    full_cdn_path = await upload_file_to_cdn(image, upload_folder_path, file_name)
    return full_cdn_path


@router.get("/client/{user_id}")
async def get_feedbacklist_by_user_id(user_id: str):
    with Session(engine) as session:
        feedback_list = session.exec(
            select(T_Feedback)
            .where(T_Feedback.client_openid == user_id)
            .order_by(T_Feedback.create_time.desc())
        ).all()
    return feedback_list
