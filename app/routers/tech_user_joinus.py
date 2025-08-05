#  技师注册及审核
import os
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select, not_, or_, and_
from sqlalchemy.exc import IntegrityError
from app.core.database import engine, get_session
from app.model.t_tech_user import T_Tech_User

router = APIRouter(
    prefix="/techUserJoinUs",
    tags=["techUserJoinUs"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


class UpdateTechInfoRequest(BaseModel):
    user_nickname: str
    user_sex: str
    user_age: int
    work_phone: str
    user_city: str


# 技师注册，补充技师基本信息
@router.post("/update_info/")
async def update_tech_user_info(user_id: str, updateTechInfo: UpdateTechInfoRequest):
    try:
        with Session(engine) as session:
            statement = select(T_Tech_User).where(T_Tech_User.openid == user_id)
            users = session.exec(statement)
            user = users.first()
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            # 更新 user_phone 字段
            user.work_phone = updateTechInfo.work_phone
            user.user_sex = updateTechInfo.user_sex
            user.user_age = updateTechInfo.user_age
            user.user_nickname = updateTechInfo.user_nickname
            user.user_city = updateTechInfo.user_city
            session.add(user)
            session.commit()
            session.refresh(user)
            # return user
            return user
    except IntegrityError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/all")
def get_tech_users(session: Session = Depends(get_session)):
    techusers = session.exec(select(T_Tech_User)).all()
    return techusers


# # 查看已上线技师（管理端）
# @router.get("/alreadyJoin")
# async def read_tech_users(pageNum: int = 0, pageSize: int = 10):
#     with Session(engine) as session:
#         statement = (
#             select(T_Tech_User)
#             .where(
#                 not_(T_Tech_User.openid.like("%mock%")),
#                 not_(T_Tech_User.openid.like("%Mock%")),
#                 T_Tech_User.work_phone != "",
#                 T_Tech_User.work_phone != "string",
#             )
#             .order_by(T_Tech_User.user_id.desc())
#         )
#         users = session.exec(statement).all()
#         return users


# # 查看未上线技师（管理端）
# @router.get("/notIn")
# async def read_tech_users():
#     with Session(engine) as session:
#         statement = (
#             select(T_Tech_User)
#             .where(
#                 and_(
#                     or_(
#                         T_Tech_User.work_phone == "",  # work_phone 为空字符串
#                         T_Tech_User.work_phone.is_(None),  # work_phone 为 None
#                     ),
#                     not_(T_Tech_User.openid.like("%mock%")),  # openid 不包含 'mock'
#                     not_(T_Tech_User.openid.like("%Mock%")),  # openid 不包含 'Mock'
#                 )
#             )
#             .order_by(T_Tech_User.user_id.desc())
#         )
#         users = session.exec(statement).all()
#         return users
