#  技师工作时间信息

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, delete, or_, text
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

from app.core.database import engine, get_session
from app.core.util import (
    get_latest_available_worktime,
    get_latest_slot_id,
)
from app.model.t_tech_user_worktime import T_Tech_User_Worktime, CreateWorktimeRequest
from app.model.t_time_slots import T_Time_Slots
from app.model.t_tech_user import T_Tech_User
from logger import logger

Tech_Allowd_Setting_Worktime_Days = 5
router = APIRouter()

router = APIRouter(
    prefix="/techUserWorktime",
    tags=["techUserWorktime"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_user_worktimes(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Tech_User_Worktime)).all()
        total_count = len(total_count)
        statement = (
            select(T_Tech_User_Worktime)
            .order_by(T_Tech_User_Worktime.work_time_id)
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


@router.get("/{work_time_id}")
async def read_user_worktime(work_time_id: str):
    with Session(engine) as session:
        statement = select(T_Tech_User_Worktime).where(
            T_Tech_User_Worktime.work_time_id == work_time_id
        )
        results = session.exec(statement)
        return results.first()


@router.get("/slots/")
async def read_user_worktimes(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Time_Slots)).all()
        total_count = len(total_count)
        statement = (
            select(T_Time_Slots)
            .order_by(T_Time_Slots.slot_id)
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


@router.post("/")
async def create_user_worktime(tech_user_worktime: T_Tech_User_Worktime):
    try:
        with Session(engine) as session:
            existing_user_worktime = session.exec(
                select(T_Tech_User_Worktime).where(
                    T_Tech_User_Worktime.work_time_id == tech_user_worktime.work_time_id
                )
            ).first()
            tech_user = session.get(T_Tech_User, tech_user_worktime.tech_user_id)
            if not tech_user:
                raise HTTPException(status_code=404, detail="Tech user not found")
            time_slot = session.get(T_Time_Slots, tech_user_worktime.slot_id)
            if not time_slot:
                raise HTTPException(status_code=404, detail="Time slot not found")
            if existing_user_worktime:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(tech_user_worktime)
                session.commit()
                session.refresh(tech_user_worktime)
                return {"msg": "create sucess", "data": tech_user_worktime}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


# 保存技师工作时间，保存三天的记录，并删除当天旧的记录；tech_user_id 记录技师的openid
# response_model=List[T_Tech_User_Worktime]
# @router.post("/worktimeBlocks/")
# def create_worktime_blocks(request: CreateWorktimeRequest):
#     try:
#         with Session(engine) as session:
#             print("request.tech_user_id:", request.tech_user_id)
#             existing_tech_user = session.exec(
#                 select(T_Tech_User).where(T_Tech_User.openid == request.tech_user_id)
#             ).first()
#             if not existing_tech_user:
#                 raise HTTPException(status_code=404, detail="Tech user not found")
#             # session.execute(delete(T_Tech_User_Worktime).where(T_Tech_User_Worktime.tech_user_id == request.tech_user_id))
#             # 取出三天的时间
#             work_dates = {entry.work_date for entry in request.worktime_blocks}
#             # 将工作日期转换为 datetime 对象
#             # work_dates_dt = [datetime.strptime(date, "%Y-%m-%d") for date in work_dates]
#             # 将工作日期转换为 datetime 对象
#             work_dates_dt = []
#             for date in work_dates:
#                 # 如果 date 是字符串，则转换为 datetime
#                 if isinstance(date, str):
#                     work_dates_dt.append(datetime.strptime(date, "%Y-%m-%d"))
#                 else:
#                     work_dates_dt.append(date)
#             # 删除该员工在同一天的历史数据，获取所有工作日期
#             start_time = datetime.now()
#             delete_result = session.execute(
#                 T_Tech_User_Worktime.__table__.delete().where(
#                     (T_Tech_User_Worktime.tech_user_id == request.tech_user_id)
#                     & (T_Tech_User_Worktime.work_date.in_(work_dates_dt))
#                 )
#             )
#             deleted_count = delete_result.rowcount  # 获取删除的行数
#             session.commit()
#             end_time = datetime.now()
#             # 打印 work_dates_dt 中的日期
#             print("工作时间设定:")
#             # for work_date in work_dates_dt:
#             #     print(work_date.date())  # 输出日期部分
#             print(
#                 f"重新保存工作时间，删除旧的记录：Deleted {deleted_count} rows for tech_user_id {request.tech_user_id}."
#             )
#             print(f"Deletion time: {end_time - start_time}")


#             # 新增工作时间
#             worktime_blocks = []
#             for block in request.worktime_blocks:
#                 worktime_block = T_Tech_User_Worktime(
#                     tech_user_id=request.tech_user_id,
#                     work_date=block.work_date,
#                     slot_id=block.slot_id,
#                     active=block.active,
#                 )
#                 worktime_blocks.append(worktime_block)
#             session.add_all(worktime_blocks)
#             session.commit()
#             # 刷新并返回新创建的工作时间块
#             for block in worktime_blocks:
#                 session.refresh(block)
#             return worktime_blocks
#     except IntegrityError:
#         raise HTTPException(status_code=401, detail="other error.")
@router.post("/worktimeBlocks/")
def create_worktime_blocks(request: CreateWorktimeRequest):
    try:
        with Session(engine) as session:

            # 提取工作日期
            work_dates = set()
            for entry in request.worktime_blocks:
                if isinstance(entry.work_date, str):
                    work_dates.add(
                        datetime.strptime(entry.work_date, "%Y-%m-%d").date()
                    )
                else:
                    work_dates.add(entry.work_date.date())

            # 开始单一事务，包含删除和添加操作
            with session.begin():
                # 删除同一天的历史数据
                start_time = datetime.now()
                delete_stmt = delete(T_Tech_User_Worktime).where(
                    (T_Tech_User_Worktime.tech_user_id == request.tech_user_id)
                    & (T_Tech_User_Worktime.work_date.in_(work_dates))
                )
                session.exec(delete_stmt)
                end_time = datetime.now()

                logger.info(
                    f"重新保存工作时间，删除旧的记录。删除时间: {end_time - start_time}"
                )

                # 添加新的工作时间
                worktime_blocks = [
                    T_Tech_User_Worktime(
                        tech_user_id=request.tech_user_id,
                        work_date=block.work_date,
                        slot_id=block.slot_id,
                        active=block.active,
                    )
                    for block in request.worktime_blocks
                ]
                session.add_all(worktime_blocks)

            # 返回创建的工作时间块
            # 注意：在大数据量情况下，可以选择不刷新直接返回
            return worktime_blocks

    except IntegrityError as e:
        # 捕获外键约束错误等
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(status_code=404, detail="Tech user not found")
        raise HTTPException(
            status_code=401, detail=f"Database integrity error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# 客户读取技师当前已设置的工作时间
@router.get("/worktimeBlocks/{openid}")
def get_worktime_blocks_by_client(
    openid: str,
    session: Session = Depends(get_session),
):
    try:
        current_time = datetime.now()
        today_date = current_time.date()
        latest_available_time = get_latest_available_worktime()
        worktime_query = (
            select(T_Tech_User_Worktime)
            .join(T_Time_Slots, T_Tech_User_Worktime.slot_id == T_Time_Slots.slot_id)
            .where(
                T_Tech_User_Worktime.tech_user_id == openid,
                T_Tech_User_Worktime.work_date < today_date + timedelta(days=3),
                text(
                    """
                        CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                        CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) > :latest_available_datetime
                    """
                ).bindparams(latest_available_datetime=latest_available_time),
            )
            .order_by(T_Tech_User_Worktime.work_date, T_Time_Slots.start_time)
        )

        # 通过 openid 获取用户的 tech_user_id
        worktime_records = session.exec(worktime_query).all()
        worktime_records_modified = fill_empty_worktime_blocks(
            [worktime_record.model_dump() for worktime_record in worktime_records],
            openid,
            3,
        )
        return worktime_records_modified
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


# 技师读取技师当前已设置的工作时间
@router.get("/worktimeBlocksFromTech/{openid}")
def get_worktime_blocks_by_tech(
    openid: str,
    session: Session = Depends(get_session),
):
    try:
        latest_available_time = get_latest_available_worktime()
        current_time = datetime.now()
        today_date = current_time.date()
        worktime_query = (
            select(T_Tech_User_Worktime)
            .join(T_Time_Slots, T_Tech_User_Worktime.slot_id == T_Time_Slots.slot_id)
            .where(
                T_Tech_User_Worktime.tech_user_id == openid,
                T_Tech_User_Worktime.work_date
                # 这里没算错
                < today_date + timedelta(days=Tech_Allowd_Setting_Worktime_Days),
                text(
                    """
                        CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                        CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) > :latest_available_datetime
                    """
                ).bindparams(latest_available_datetime=latest_available_time),
            )
            .order_by(T_Tech_User_Worktime.work_date, T_Time_Slots.start_time)
        )

        # 通过 openid 获取用户的 tech_user_id
        worktime_records = session.exec(worktime_query).all()
        worktime_records_modified = fill_empty_worktime_blocks(
            [worktime_record.model_dump() for worktime_record in worktime_records],
            openid,
            Tech_Allowd_Setting_Worktime_Days,
        )
        return worktime_records_modified
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_user_worktime(work_time_id: int, newOrderProd: T_Tech_User_Worktime):
    with Session(engine) as session:
        statement = select(T_Tech_User_Worktime).where(
            T_Tech_User_Worktime.work_time_id == work_time_id
        )
        result = session.exec(statement)
        user_worktime = result.one()
        user_worktime.tech_user_id = newOrderProd.tech_user_id
        user_worktime.slot_id = newOrderProd.slot_id
        user_worktime.work_date = newOrderProd.work_date
        user_worktime.active = newOrderProd.active
        session.add(user_worktime)
        session.commit()
        session.refresh(user_worktime)
        return user_worktime


@router.post("/del/{work_time_id}")
async def delete_user_worktime(work_time_id: int):
    with Session(engine) as session:
        statement = select(T_Tech_User_Worktime).where(
            T_Tech_User_Worktime.work_time_id == work_time_id
        )
        results = session.exec(statement)
        user_worktime = results.first()
        if not user_worktime:
            return {"msg": "there's no user_worktime", "data": ""}
        session.delete(user_worktime)
        session.commit()
        return {"msg": "delete sucess", "data": user_worktime}


def fill_empty_worktime_blocks(worktime_records, openid, days):
    # 添加空的工作时间块
    work_dates = [record["work_date"] for record in worktime_records]
    start_date = datetime.today().date()
    current_dates = [start_date + timedelta(days=i) for i in range(days)]
    for date in current_dates:
        if date not in work_dates:
            if date == datetime.today().date():
                latest_slot_id = get_latest_slot_id()
                if latest_slot_id:
                    for i in range(latest_slot_id, 49):
                        new_worktime_record = {
                            "work_date": date,
                            "tech_user_id": openid,
                            "slot_id": i,
                            "active": False,
                        }
                        worktime_records.append(new_worktime_record)
            else:
                for i in range(1, 49):
                    new_worktime_record = {
                        "work_date": date,
                        "tech_user_id": openid,
                        "slot_id": i,
                        "active": False,
                    }
                    worktime_records.append(new_worktime_record)
    return worktime_records
