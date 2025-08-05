from datetime import datetime, timedelta
from sqlalchemy import delete, or_, text, func
from sqlmodel import Session, select

from app.core.util import get_latest_available_worktime
from app.model.t_tech_busy_time import T_Tech_Busy_Time
from app.model.t_tech_user_worktime import T_Tech_User_Worktime
from app.model.t_time_slots import T_Time_Slots


def get_next_worktimes_query(is_subquery: bool = True, tech_openid: str = None):
    tomorrow = datetime.now() + timedelta(days=1)
    latest_available_time = get_latest_available_worktime()
    next_worktimes_query = (
        select(
            T_Tech_User_Worktime.tech_user_id,
            T_Tech_User_Worktime.work_date,
            T_Time_Slots.start_time,
            T_Time_Slots.end_time,
            func.row_number()
            .over(
                partition_by=T_Tech_User_Worktime.tech_user_id,
                order_by=[
                    T_Tech_User_Worktime.work_date,  # 首先按工作日期排序
                    T_Tech_User_Worktime.slot_id,  # 然后按slot_id排序
                ],
            )
            .label("rn"),
        )
        .join(T_Time_Slots, T_Tech_User_Worktime.slot_id == T_Time_Slots.slot_id)
        .outerjoin(
            T_Tech_Busy_Time,
            T_Tech_User_Worktime.tech_user_id == T_Tech_Busy_Time.tech_user_openid,
        )
        .where(
            # or_(
            #     T_Tech_User_Worktime.work_date > current_date,  # 未来的日期
            #     and_(
            #         T_Tech_User_Worktime.work_date == current_date,  # 今天的日期
            #         T_Time_Slots.start_time
            #         > latest_available_time,  # 但是时间在当前之后
            #     ),
            # ),
            text(
                """
                        CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' +
                        CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) > :latest_available_datetime
                    """
            ).bindparams(latest_available_datetime=latest_available_time),
            text(
                """
                    CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                    CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) < :tomorrow
                """
            ).bindparams(tomorrow=tomorrow),
            text(
                """     
                    (
                        t_tech_busy_time.tech_user_openid IS NULL
                        OR
                        (
                            -- 检查工作时间是否与忙碌时间重叠
                            CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                            CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) <= t_tech_busy_time.start_time
                            OR
                            CAST(CONVERT(VARCHAR, t_tech_user_worktime.work_date, 23) + ' ' + 
                            CONVERT(VARCHAR, t_time_slots.start_time, 108) AS DATETIME) >= t_tech_busy_time.end_time
                        )
                    )
                """
            ),
            T_Tech_User_Worktime.active == 1,
        )
    )
    if is_subquery:
        next_worktimes_query = next_worktimes_query.subquery()
    else:
        next_worktimes_query = next_worktimes_query.where(
            T_Tech_User_Worktime.tech_user_id == tech_openid
        )
    return next_worktimes_query


def delete_tech_busy_time(order_id: int, session: Session, need_commit: bool = False):
    tech_busy_time_statement = select(T_Tech_Busy_Time).where(
        or_(
            T_Tech_Busy_Time.order_id == order_id,
            T_Tech_Busy_Time.parent_order_id == order_id,
        )
    )
    start_time = None
    end_time = None
    tech_busy_time: T_Tech_Busy_Time = session.exec(tech_busy_time_statement).first()
    if tech_busy_time:
        start_time = tech_busy_time.start_time
        end_time = tech_busy_time.end_time
    delete_stmt = delete(T_Tech_Busy_Time).where(
        or_(
            T_Tech_Busy_Time.order_id == order_id,
            T_Tech_Busy_Time.parent_order_id == order_id,
        )
    )
    session.exec(delete_stmt)
    if need_commit:
        session.commit()
    return start_time, end_time
