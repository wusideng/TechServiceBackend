#  订单信息

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine, get_session
from app.lib.utils.order import get_all_todo_orders_count_func
from app.model.t_apply_status import T_Apply_Status
from app.model.t_recruit import T_Recruit
from app.model.t_sys_user import T_Sys_User
from app.model.t_tech_user_contract import T_Tech_USER_Contract

router = APIRouter()

router = APIRouter(
    prefix="/sysUser",
    tags=["sysUser"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/users")
async def read_sys_users(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Sys_User)).all()
        total_count = len(total_count)
        statement = (
            select(T_Sys_User)
            .order_by(T_Sys_User.user_id)
            .offset(offset)
            .limit(pageSize)
        )
        orders = session.exec(statement).all()
        return {
            "total_count": total_count,
            "data": orders,
            "page": pageNum,
            "page_size": pageSize,
            "total_pages": (total_count // pageSize)
            + (1 if total_count % pageSize > 0 else 0),
        }


@router.get("/users/{user_id}")
async def read_sys_user(user_id: str):
    with Session(engine) as session:
        statement = select(T_Sys_User).where(T_Sys_User.user_id == user_id)
        results = session.exec(statement)
        return results.first()


@router.post("/users/")
async def create_sys_user(sysUser: T_Sys_User):
    try:
        with Session(engine) as session:
            existing_sys_user = session.exec(
                select(T_Sys_User).where(T_Sys_User.user_id == sysUser.user_id)
            ).first()
            if existing_sys_user:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(sysUser)
                session.commit()
                session.refresh(sysUser)
                return {"msg": "create sucess", "data": sysUser}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/users/")
async def update_sys_user(user_id: int, newOrderProd: T_Sys_User):
    with Session(engine) as session:
        statement = select(T_Sys_User).where(T_Sys_User.user_id == user_id)
        result = session.exec(statement)
        user_auth = result.one()
        user_auth.user_id = newOrderProd.user_id
        user_auth.user_nickname = newOrderProd.user_nickname
        user_auth.user_photo = newOrderProd.user_photo
        session.add(user_auth)
        session.commit()
        session.refresh(user_auth)
        return user_auth


@router.post("/users/del/{user_id}")
async def delete_sys_user(user_id: int):
    with Session(engine) as session:
        statement = select(T_Sys_User).where(T_Sys_User.user_id == user_id)
        results = session.exec(statement)
        user_auth = results.first()
        if not user_auth:
            return {"msg": "there's no user_auth", "data": ""}
        session.delete(user_auth)
        session.commit()
        return {"msg": "delete sucess", "data": user_auth}


@router.get("/initial_info")
async def get_initial_info_from_city_manager(session=Depends(get_session)):
    statement = (
        select(T_Apply_Status.apply_type, func.count(T_Apply_Status.apply_type))
        .where(T_Apply_Status.apply_status == "apply")
        .group_by(T_Apply_Status.apply_type)
    )
    apply_status_count_dict = {}
    results = session.exec(statement).all()
    for row in results:
        apply_status_count_dict[row[0]] = row[1]
    contract_count = session.exec(
        select(func.count())
        .select_from(T_Tech_USER_Contract)
        .where(T_Tech_USER_Contract.status == "apply")
    ).one()
    order_count = get_all_todo_orders_count_func(session)
    recruit_count = session.exec(
        select(func.count())
        .select_from(T_Recruit)
        .where(T_Recruit.has_contacted != True)
    ).one()
    return {
        "order_count": order_count,
        "apply_status_count": apply_status_count_dict,
        "contract_count": contract_count,
        "recruit_count": recruit_count,
    }
