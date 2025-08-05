#  申请流程信息

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.core.database import engine, get_session
from app.lib.utils.upload import upload_file_to_cdn
from app.model.t_apply_status import T_Apply_Status
from app.model.t_tech_user import T_Tech_User

router = APIRouter()

router = APIRouter(
    prefix="/applyStatus",
    tags=["applyStatus"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


# 申请信息查看（管理端查看全部申请嘻嘻）
@router.get("/")
async def read_apply_statuses():
    with Session(engine) as session:
        statement = select(T_Apply_Status).order_by(T_Apply_Status.apply_id.desc())
        apply_statuses = session.exec(statement).all()
        return apply_statuses


# 申请信息查看（技师端，查看本人审批记录）
@router.get("/tech/{tech_id}")
async def read_apply_status(tech_id: str):
    with Session(engine) as session:
        statement = (
            select(T_Apply_Status)
            .where(T_Apply_Status.tech_id == tech_id)
            .order_by(T_Apply_Status.updateTime.desc())
        )
        results = session.exec(statement).all()
        return results


# 申请信息查看（技师端，查看本人审批记录）
@router.get("/tech_applying/{tech_id}")
async def read_apply_status(tech_id: str):
    with Session(engine) as session:
        statement = (
            select(T_Apply_Status)
            .where(
                T_Apply_Status.tech_id == tech_id,
                T_Apply_Status.apply_status == "apply",
            )
            .order_by(T_Apply_Status.updateTime.desc())
        )
        results = session.exec(statement).all()
        return results


# 查看全部待审核信息(管理端，进行审批提醒)
@router.get("/apply")
async def read_apply_status():
    with Session(engine) as session:
        statement = (
            select(T_Apply_Status)
            .where(T_Apply_Status.apply_status == "apply")
            .order_by(T_Apply_Status.apply_id.desc())
        )
        apply_statuses = session.exec(statement).all()
        return apply_statuses


# 待审核信息查看（管理端，待审批信息查看）
@router.get("/apply/{apply_type}")
async def read_apply_status(apply_type: str):
    with Session(engine) as session:
        statement = (
            select(T_Apply_Status)
            .where(
                T_Apply_Status.apply_status == "apply",
                T_Apply_Status.apply_type == apply_type,
            )
            .order_by(T_Apply_Status.apply_id.desc())
        )
        apply_statuses = session.exec(statement).all()
        return apply_statuses


# 已审核信息查看（管理端，审批历史查看）
@router.get("/applied/{apply_type}")
async def read_applied_status(apply_type: str):
    with Session(engine) as session:
        statement = (
            select(T_Apply_Status)
            .where(
                or_(
                    T_Apply_Status.apply_status == "approve",
                    T_Apply_Status.apply_status == "reject",
                ),
                T_Apply_Status.apply_type == apply_type,
            )
            .order_by(T_Apply_Status.updateTime.desc())
        )
        apply_statuses = session.exec(statement).all()
        return apply_statuses


# 新建申请信息（技师端，上线申请）
@router.post("/")
async def create_apply_status(apply_status: T_Apply_Status):
    try:
        with Session(engine) as session:
            existing_apply_status = session.exec(
                select(T_Apply_Status).where(
                    T_Apply_Status.tech_id == apply_status.tech_id,
                    T_Apply_Status.apply_status == "apply",
                    T_Apply_Status.apply_type == "tech_join",
                )
            ).first()
            if existing_apply_status:
                raise HTTPException(
                    status_code=500,
                    detail="申请已经提交，正在审批处理，如需加急，请联系城市管理员.",
                )
            else:
                session.add(apply_status)
                session.commit()
                session.refresh(apply_status)
                return {"msg": "create sucess", "data": apply_status}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


# 提交技师工作照（技师端，审核申请）
@router.post("/workPhoto/{openid}")
async def create_apply_workphoto_status(
    openid: str, photo_work: UploadFile = File(None)
):
    try:
        with Session(engine) as session:
            if not photo_work.filename.endswith((".png", ".jpg", ".jpeg")):
                raise HTTPException(
                    status_code=401, detail="Invalid photo_work format."
                )
            statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
            existing_tech = session.exec(statement).first()
            if not existing_tech:
                raise HTTPException(
                    status_code=401, detail="请先授权上线再上传工作照片."
                )
            elif (
                existing_tech.user_nickname == ""
                or existing_tech.user_nickname == "string"
            ):
                raise HTTPException(
                    status_code=402,
                    detail="请先申请注册，注册成为在线技师后，再上传工作照片.",
                )
            existing_apply_status = session.exec(
                select(T_Apply_Status).where(
                    T_Apply_Status.tech_id == openid,
                    T_Apply_Status.apply_status == "apply",
                    T_Apply_Status.apply_type == "tech_workphoto",
                )
            ).first()
            if existing_apply_status:
                raise HTTPException(
                    status_code=500,
                    detail="申请已经提交，正在审批处理，如需加急，请联系城市管理员.",
                )
            else:
                print("upload0:", openid)
                print("upload1:", photo_work)
                cdn_path = await upload_photo_to_cdn(
                    photo_work, openid, existing_tech.user_nickname
                )
                # cdn_path = await upload_photo_to_local(photo_work, openid, existing_tech.user_nickname)
                print("cdn_path:", cdn_path)
                # 创建新的 apply_status 实例
                new_apply_status = T_Apply_Status(
                    tech_id=openid,
                    apply_status="apply",  # 审批状态
                    apply_type="tech_workphoto",  # 申请类型
                    user_nickname=existing_tech.user_nickname,
                    user_city=existing_tech.user_city,
                    user_age=existing_tech.user_age,
                    user_sex=existing_tech.user_sex,
                    work_phone=existing_tech.work_phone,
                    photo_work=cdn_path,
                )
                # 添加到会话并提交
                session.add(new_apply_status)
                session.commit()
                session.refresh(new_apply_status)
                return new_apply_status
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


# 提交技师生活照（技师端，审核申请）
@router.post("/lifePhoto/{openid}")
async def create_apply_lifephoto_status(
    openid: str,
    photo_life_1: UploadFile = File(None),
    photo_life_2: UploadFile = File(None),
    photo_life_3: UploadFile = File(None),
):
    try:
        with Session(engine) as session:
            if not photo_life_1.filename.endswith((".png", ".jpg", ".jpeg")):
                raise HTTPException(
                    status_code=401, detail="Invalid photo_life_1 format."
                )

            statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
            existing_tech = session.exec(statement).first()
            if not existing_tech:
                raise HTTPException(
                    status_code=401, detail="请先授权上线再上传工作照片."
                )
            elif (
                existing_tech.user_nickname == ""
                or existing_tech.user_nickname == "string"
            ):
                raise HTTPException(
                    status_code=402,
                    detail="请先申请注册，注册成为在线技师后，再上传工作照片.",
                )
            existing_apply_status = session.exec(
                select(T_Apply_Status).where(
                    T_Apply_Status.tech_id == openid,
                    T_Apply_Status.apply_status == "apply",
                    T_Apply_Status.apply_type == "tech_lifephoto",
                )
            ).first()
            if existing_apply_status:
                raise HTTPException(
                    status_code=403,
                    detail="申请已经提交，正在审批处理，如需加急，请联系城市管理员.",
                )
            else:
                print("upload")
                cdn_path1 = await upload_photo_to_cdn(
                    photo_life_1, openid, existing_tech.user_nickname
                )
                cdn_path2 = await upload_photo_to_cdn(
                    photo_life_2, openid, existing_tech.user_nickname
                )
                cdn_path3 = await upload_photo_to_cdn(
                    photo_life_3, openid, existing_tech.user_nickname
                )
                # cdn_path = await upload_photo_to_local(photo_work, openid, existing_tech.user_nickname)
                # 创建新的 apply_status 实例
                new_apply_status = T_Apply_Status(
                    tech_id=openid,
                    apply_status="apply",  # 审批状态
                    apply_type="tech_lifephoto",  # 申请类型
                    user_nickname=existing_tech.user_nickname,
                    user_city=existing_tech.user_city,
                    user_age=existing_tech.user_age,
                    user_sex=existing_tech.user_sex,
                    work_phone=existing_tech.work_phone,
                    photo_life_1=cdn_path1,
                    photo_life_2=cdn_path2,
                    photo_life_3=cdn_path3,
                )
                # 添加到会话并提交
                session.add(new_apply_status)
                session.commit()
                session.refresh(new_apply_status)
                return new_apply_status
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


# 技师端执照申请
@router.post("/certificate/{openid}")
async def create_apply_certificate_status(
    openid: str,
    business_license_file: UploadFile = File(None),
    technician_certificate_file: UploadFile = File(None),
    health_certificate_file: UploadFile = File(None),
    session=Depends(get_session),
):
    try:
        statement = select(T_Tech_User).where(T_Tech_User.openid == openid)
        existing_tech = session.exec(statement).first()
        # 上传证件信息，判断技师是否已经申请注册通过
        if not existing_tech:
            raise HTTPException(status_code=401, detail="请先授权上线再上传证件信息.")
        elif (
            existing_tech.user_nickname == "" or existing_tech.user_nickname == "string"
        ):
            raise HTTPException(
                status_code=402,
                detail="请先申请注册，注册成为在线技师后，再上传证件信息.",
            )
        # 提交申请信息，判断是否有正在审批的证件信息申请，如果有则不重复提交
        existing_apply_status = session.exec(
            select(T_Apply_Status).where(
                T_Apply_Status.tech_id == openid,
                T_Apply_Status.apply_status == "apply",
                T_Apply_Status.apply_type == "tech_certificate",
            )
        ).first()
        if existing_apply_status:
            raise HTTPException(
                status_code=403,
                detail="申请已经提交，正在审批处理，如需加急，请联系城市管理员.",
            )
        else:
            businiess_license_cdnpath = None
            technician_certificate_cdnpath = None
            health_certificate_cdnpath = None
            if business_license_file:
                businiess_license_cdnpath = await upload_photo_to_cdn(
                    business_license_file,
                    openid,
                    "商户执照_" + existing_tech.user_nickname,
                )
                print("上传商户执照：", businiess_license_cdnpath)
            if technician_certificate_file:
                technician_certificate_cdnpath = await upload_photo_to_cdn(
                    technician_certificate_file,
                    openid,
                    "技师证_" + existing_tech.user_nickname,
                )
                print("上传技师证：", technician_certificate_cdnpath)
            if health_certificate_file:
                health_certificate_cdnpath = await upload_photo_to_cdn(
                    health_certificate_file,
                    openid,
                    "健康证_" + existing_tech.user_nickname,
                )
                print("上传健康证：", health_certificate_cdnpath)

            # cdn_path = await upload_photo_to_local(photo_work, openid, existing_tech.user_nickname)
            # 创建新的 apply_status 实例
            new_apply_status = T_Apply_Status(
                tech_id=openid,
                apply_status="apply",  # 审批状态
                apply_type="tech_certificate",  # 申请类型
                user_nickname=existing_tech.user_nickname,
                user_city=existing_tech.user_city,
                user_age=existing_tech.user_age,
                user_sex=existing_tech.user_sex,
                work_phone=existing_tech.work_phone,
                business_license=businiess_license_cdnpath,
                technician_certificate=technician_certificate_cdnpath,
                health_certificate=health_certificate_cdnpath,
            )
            # 添加到会话并提交
            session.add(new_apply_status)
            session.commit()
            session.refresh(new_apply_status)
            return new_apply_status
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/modify/")
async def update_apply_status(apply_id: int, newApplyStatus: T_Apply_Status):
    with Session(engine) as session:
        statement = select(T_Apply_Status).where(T_Apply_Status.apply_id == apply_id)
        result = session.exec(statement)
        apply_res = result.one()
        apply_res.apply_status = newApplyStatus.apply_status
        apply_res.apply_refuse_cause = newApplyStatus.apply_refuse_cause
        apply_res.work_phone = newApplyStatus.work_phone
        apply_res.user_nickname = newApplyStatus.user_nickname
        apply_res.user_sex = newApplyStatus.user_sex
        apply_res.user_age = newApplyStatus.user_age
        apply_res.user_city = newApplyStatus.user_city
        apply_res.photo_work = newApplyStatus.photo_work
        apply_res.photo_life_1 = newApplyStatus.photo_life_1
        apply_res.photo_life_2 = newApplyStatus.photo_life_2
        apply_res.photo_life_3 = newApplyStatus.photo_life_3
        apply_res.business_license = newApplyStatus.business_license
        apply_res.technician_certificate = newApplyStatus.technician_certificate
        apply_res.health_certificate = newApplyStatus.health_certificate
        apply_res.updateTime = datetime.now()
        session.add(apply_res)
        session.commit()
        session.refresh(apply_res)
        return apply_res


@router.post("/del/{apply_id}")
async def delete_apply_status(apply_id: int):
    with Session(engine) as session:
        statement = select(T_Apply_Status).where(T_Apply_Status.apply_id == apply_id)
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}


async def upload_photo_to_cdn(photo: UploadFile, user_id: str, user_nickname: str):
    photo_filename = "Tech_User_" + user_id + "_" + user_nickname + "_" + photo.filename
    upload_cdn_folder_path = "uploads"
    cdn_path = await upload_file_to_cdn(photo, upload_cdn_folder_path, photo_filename)
    return cdn_path
