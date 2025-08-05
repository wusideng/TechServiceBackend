#  订单信息

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.model.t_tech_user_auth import T_Tech_User_Auth

router = APIRouter()

router = APIRouter(
    prefix="/techUserAuth",
    tags=["techUserAuth"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_user_auths(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Tech_User_Auth)).all()
        total_count = len(total_count)
        statement = (
            select(T_Tech_User_Auth)
            .order_by(T_Tech_User_Auth.auth_id)
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


@router.get("/{auth_id}")
async def read_user_auth(auth_id: str):
    with Session(engine) as session:
        statement = select(T_Tech_User_Auth).where(T_Tech_User_Auth.auth_id == auth_id)
        results = session.exec(statement)
        return results.first()


@router.post("/")
async def create_user_auth(order_comment: T_Tech_User_Auth):
    try:
        with Session(engine) as session:
            existing_user_auth = session.exec(
                select(T_Tech_User_Auth).where(
                    T_Tech_User_Auth.auth_id == order_comment.auth_id
                )
            ).first()
            if existing_user_auth:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(order_comment)
                session.commit()
                session.refresh(order_comment)
                return {"msg": "create sucess", "data": order_comment}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_user_auth(auth_id: int, newOrderProd: T_Tech_User_Auth):
    with Session(engine) as session:
        statement = select(T_Tech_User_Auth).where(T_Tech_User_Auth.auth_id == auth_id)
        result = session.exec(statement)
        user_auth = result.one()
        user_auth.user_id = newOrderProd.user_id
        user_auth.auth_type = newOrderProd.auth_type
        user_auth.openid = newOrderProd.openid
        user_auth.access_token = newOrderProd.access_token
        session.add(user_auth)
        session.commit()
        session.refresh(user_auth)
        return user_auth


@router.post("/del/{auth_id}")
async def delete_user_auth(auth_id: int):
    with Session(engine) as session:
        statement = select(T_Tech_User_Auth).where(T_Tech_User_Auth.auth_id == auth_id)
        results = session.exec(statement)
        user_auth = results.first()
        if not user_auth:
            return {"msg": "there's no user_auth", "data": ""}
        session.delete(user_auth)
        session.commit()
        return {"msg": "delete sucess", "data": user_auth}
