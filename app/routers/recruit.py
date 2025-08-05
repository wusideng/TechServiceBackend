from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from sqlmodel import Session, select
from sqlalchemy import func

from app.core.database import engine, get_session
from app.model.q_Recruit import UpdateRecruitRequest
from app.model.t_recruit import T_Recruit


router = APIRouter(
    prefix="/recruit",
    tags=["recruit"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.post("/")
# 客户端申请
async def add_recruit(
    values: dict,
    session: Session = Depends(get_session),
):
    recruit = T_Recruit(**values)
    session.add(recruit)
    session.commit()
    return Response(status_code=200)


@router.put("/")
# 客户端申请
async def update_recruit(
    values: UpdateRecruitRequest,
    session: Session = Depends(get_session),
):
    recruit = session.exec(select(T_Recruit).where(T_Recruit.id == values.id)).first()

    recruit.has_contacted = values.has_contacted
    recruit.remark = values.remark
    session.commit()
    return Response(status_code=200)


@router.get("/")
async def recruit(
    pageNumber: int,
    pageSize: int,
    session=Depends(get_session),
):
    offset_value = (pageNumber - 1) * pageSize
    statement_init = select(T_Recruit).order_by(T_Recruit.create_time.desc())
    count_query = select(func.count()).select_from(statement_init.alias())
    statement = statement_init.limit(pageSize).offset(offset_value)
    apply_list = session.exec(statement).all()
    count = session.exec(count_query).first()

    return {
        "data": apply_list,
        "totalCount": count,
        "currentPage": pageNumber,
        "pageSize": pageSize,
    }
