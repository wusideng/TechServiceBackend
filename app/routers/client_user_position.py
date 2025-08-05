# 顾客位置
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.model.t_client_user_position import T_Client_User_Position

router = APIRouter(
    prefix="/clientUserPosition",
    tags=["clientUserPosition"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Nost found"}},
)


@router.get("/")
async def read_positions(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Client_User_Position)).all()
        total_count = len(total_count)
        statement = (
            select(T_Client_User_Position)
            .order_by(T_Client_User_Position.client_user_position_id)
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


@router.get("/{client_user_position_id}")
async def read_position(client_user_position_id: str):
    with Session(engine) as session:
        statement = select(T_Client_User_Position).where(
            T_Client_User_Position.client_user_position_id == client_user_position_id
        )
        results = session.exec(statement)
        return results.first()


# 添加顾客位置信息时，取出位置信息中城市字段保存到顾客表中
# address: "北京市昌平区城北街道中共北京市昌平区委员会昌平区人民政府"
# city: "北京市-昌平区"
# client_openid: "oK9p06eiEk0jWNvowVjb5lGlkocM"
# detail_address: ""
# lat: 40.22077
# lon: 116.23128
@router.post("/")
async def create_position(position: T_Client_User_Position):
    try:
        with Session(engine) as session:
            # existing_position = session.exec(
            #     select(T_Client_User_Position).where(
            #         T_Client_User_Position.client_user_position_id
            #         == position.client_user_position_id
            #     )
            # ).first()
            # if existing_position:
            #     raise HTTPException(
            #         status_code=400,
            #         detail="Item with this unique field already exists.",
            #     )
            session.add(position)
            session.commit()
            session.refresh(position)

            # 更新 T_Client_User 中的 city 字段
            # user_result = session.exec(
            #     select(T_Client_User).where(
            #         T_Client_User.openid == position.client_openid
            #     )
            # )
            # user = user_result.first()
            # if user:
            #     user.user_city = position.city  # 更新 city
            #     user.user_location = position.address
            #     session.add(user)  # 添加更新的用户
            #     session.commit()  # 提交更改
            #     logger.info(
            #         f"Updated city to '{position.city }' for user ID {position.client_openid}."
            #     )
            # else:
            #     logger.info(f"No user found with ID {position.client_openid}.")
            return {"msg": "create sucess", "data": position}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_position(
    client_user_position_id: int, newPositon: T_Client_User_Position
):
    with Session(engine) as session:
        statement = select(T_Client_User_Position).where(
            T_Client_User_Position.client_user_position_id == client_user_position_id
        )
        result = session.exec(statement)
        position = result.one()
        position.client_openid = newPositon.client_openid
        position.refresh_time = newPositon.refresh_time
        position.lon = newPositon.lon
        position.lat = newPositon.lat
        position.address = newPositon.address
        position.city = newPositon.city
        position.detail_address = newPositon.detail_address
        session.add(position)
        session.commit()
        session.refresh(position)
        return position


@router.post("/del/{client_user_position_id}")
async def delete_position(client_user_position_id: int):
    with Session(engine) as session:
        statement = select(T_Client_User_Position).where(
            T_Client_User_Position.client_user_position_id == client_user_position_id
        )
        results = session.exec(statement)
        position = results.first()
        if not position:
            return {"msg": "there's no position", "data": ""}
        session.delete(position)
        session.commit()
        return {"msg": "delete sucess", "data": position}
