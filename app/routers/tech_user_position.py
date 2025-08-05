# #  技师位置
# from fastapi import APIRouter, HTTPException
# from sqlmodel import Session, select
# from sqlalchemy.exc import IntegrityError

# from app.core.database import engine
# from app.model.t_tech_user_position import T_Tech_User_Position

# router = APIRouter(
#     prefix="/techUserPosition",
#     tags=["techUserPosition"],
#     # dependencies=[Depends(get_sys_token_header)],
#     # responses={404: {"description": "Nost found"}},
# )


# @router.get("/")
# async def read_positions(pageNum: int = 0, pageSize: int = 10):
#     with Session(engine) as session:
#         offset = pageNum * pageSize
#         total_count = session.exec(select(T_Tech_User_Position)).all()
#         total_count = len(total_count)
#         statement = (
#             select(T_Tech_User_Position)
#             .order_by(T_Tech_User_Position.tech_user_position_id)
#             .offset(offset)
#             .limit(pageSize)
#         )
#         orders = session.exec(statement).all()
#         return {
#             "total_count": total_count,
#             "data": orders,
#             "page": pageNum,
#             "page_size": pageSize,
#             "total_pages": (total_count // pageSize)
#             + (1 if total_count % pageSize > 0 else 0),
#         }


# @router.get("/{tech_user_position_id}")
# async def read_position(tech_user_position_id: str):
#     with Session(engine) as session:
#         statement = select(T_Tech_User_Position).where(
#             T_Tech_User_Position.tech_user_position_id == tech_user_position_id
#         )
#         results = session.exec(statement)
#         return results.first()

# @router.get("/tech/{openid}")
# async def read_position(openid: str, pageNum: int = 0, pageSize: int = 10):
#     with Session(engine) as session:
#         offset = pageNum * pageSize
#         total_count = session.exec(select(T_Tech_User_Position).where(T_Tech_User_Position.tech_user_id == openid)).all()
#         total_count = len(total_count)
#         statement = select(T_Tech_User_Position).where(
#             T_Tech_User_Position.tech_user_id == openid
#         ).order_by(T_Tech_User_Position.refresh_time.desc()).offset(offset).limit(pageSize)
#         results = session.exec(statement).all()
#         return {
#             "total_count": total_count,
#             "data": results,
#             "page": pageNum,
#             "page_size": pageSize,
#             "total_pages": (total_count // pageSize)
#             + (1 if total_count % pageSize > 0 else 0),
#         }


# @router.post("/")
# async def create_position(position: T_Tech_User_Position):
#     try:
#         with Session(engine) as session:
#             existing_position = session.exec(
#                 select(T_Tech_User_Position).where(
#                     T_Tech_User_Position.tech_user_position_id
#                     == position.tech_user_position_id
#                 )
#             ).first()
#             if existing_position:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Item with this unique field already exists.",
#                 )
#             else:
#                 session.add(position)
#                 session.commit()
#                 session.refresh(position)
#                 return {"msg": "create sucess", "data": position}
#     except IntegrityError:
#         raise HTTPException(status_code=401, detail="other error.")


# @router.put("/")
# async def update_position(tech_user_position_id: int, newPositon: T_Tech_User_Position):
#     with Session(engine) as session:
#         statement = select(T_Tech_User_Position).where(
#             T_Tech_User_Position.tech_user_position_id == tech_user_position_id
#         )
#         result = session.exec(statement)
#         position = result.one()
#         position.tech_user_id = newPositon.tech_user_id
#         position.refresh_time = newPositon.refresh_time
#         position.lon = newPositon.lon
#         position.lat = newPositon.lat
#         position.address = newPositon.address
#         position.work_city = newPositon.work_city
#         position.work_position = newPositon.work_position
#         position.sub_position = newPositon.sub_position
#         position.work_range = newPositon.work_range
#         session.add(position)
#         session.commit()
#         session.refresh(position)
#         return position


# @router.post("/del/{tech_user_position_id}")
# async def delete_position(tech_user_position_id: int):
#     with Session(engine) as session:
#         statement = select(T_Tech_User_Position).where(
#             T_Tech_User_Position.tech_user_position_id == tech_user_position_id
#         )
#         results = session.exec(statement)
#         position = results.first()
#         if not position:
#             return {"msg": "there's no position", "data": ""}
#         session.delete(position)
#         session.commit()
#         return {"msg": "delete sucess", "data": position}
