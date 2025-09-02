#  账单信息
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlalchemy import select, func, and_, desc, exists, or_
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
from datetime import datetime, timedelta

import traceback

from app.core.database import engine, get_session
from app.model.t_bill import T_Bill
from app.model.t_order import T_Order
from app.model.t_tech_user import T_Tech_User
from app.model.t_order_product import T_Order_Product

from logger import logger

router = APIRouter()

router = APIRouter(
    prefix="/bill",
    tags=["bill"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_bills():
    with Session(engine) as session:
        statement = select(T_Bill).order_by(T_Bill.bill_id)
        orders = session.exec(statement).all()
        return orders


@router.get("/{bill_id}")
async def read_bill(bill_id: str):
    with Session(engine) as session:
        statement = select(T_Bill).where(T_Bill.bill_id == bill_id)
        results = session.exec(statement)
        return results.first()


# 技师钱包详细列表
@router.get("/tech/{openid}")
async def read_bill_by_tech(openid: str):
    with Session(engine) as session:
        statement = select(T_Bill).where(T_Bill.openid == openid)
        results = session.exec(statement)
        return results.first()


@router.get("/tech/{openid}")
async def read_bill_by_tech(openid: str):
    with Session(engine) as session:
        statement = select(T_Bill).where(T_Bill.openid == openid)
        results = session.exec(statement)
        return results.first()


# 技师收入统计，用于技师钱包展示
@router.get("/tech_benefit_detail/{openid}")
async def get_tech_benefit_detail(openid: str, session=Depends(get_session)):
    # 第一次查询：获取主订单和对应的bill
    orders_bills = session.exec(
        select(T_Order, T_Bill)
        .join(T_Bill, T_Bill.order_id == T_Order.order_id)
        .where(T_Bill.openid == openid)
        .order_by(desc(T_Order.service_time))
    ).all()

    if not orders_bills:
        return []

    main_order_ids = [order.order_id for order, _ in orders_bills]

    # 第二次查询：获取子订单映射关系
    child_orders = session.exec(
        select(T_Order.order_id, T_Order.parent_order_id).where(
            T_Order.parent_order_id.in_(main_order_ids)
        )
    ).all()

    # 构建order_id到main_order_id的映射
    order_to_main = {}
    # 主订单映射到自己
    for order, _ in orders_bills:  # 修正：直接使用order对象
        order_to_main[order.order_id] = order.order_id  # 修正：使用order.order_id
    # 子订单映射到父订单
    for child_id, parent_id in child_orders:
        order_to_main[child_id] = parent_id
    # 第三次查询：一次性获取所有相关products
    all_order_ids = list(order_to_main.keys())
    all_products = session.exec(
        select(T_Order_Product)
        .where(T_Order_Product.order_id.in_(all_order_ids))
        .order_by(T_Order_Product.order_time)
    ).all()

    # 按主订单分组products
    products_by_main_order = {
        order.order_id: [] for order, _ in orders_bills
    }  # 修正：使用order.order_id
    for product in all_products:
        main_order_id = order_to_main[product.order_id]
        products_by_main_order[main_order_id].append(product)
    # 构建最终结果：(order, bill, products) 的列表

    results = []
    for order, bill in orders_bills:
        products = products_by_main_order[order.order_id]
        results.append((order, bill, products))
    return results


# 技师收入统计，用于技师钱包展示
@router.get("/techSum/{openid}")
async def read_bill_by_tech_sum(openid: str):
    with Session(engine) as session:
        statement = select(T_Bill).where(T_Bill.openid == openid)
        results = session.exec(statement).all()
        total_product_unpaid_income = sum(
            bill.tech_income for bill in results if bill.withdrawed is False
        )
        total_product_paid_income = sum(
            bill.tech_income for bill in results if bill.withdrawed is True
        )
        total_travel_unpaid = sum(
            bill.travel_cost for bill in results if bill.withdrawed is False
        )
        total_travel_paid = sum(
            bill.travel_cost for bill in results if bill.withdrawed is True
        )

        return {
            "total_product_unpaid_income": total_product_unpaid_income,
            "total_product_paid_income": total_product_paid_income,
            "total_travel_unpaid": total_travel_unpaid,
            "total_travel_paid": total_travel_paid,
        }


# 技师服务完成增加一条账单信息
@router.post("/")
async def create_bill(bill: T_Bill):
    try:
        with Session(engine) as session:
            existing_order = session.exec(
                select(T_Bill).where(T_Bill.bill_id == bill.bill_id)
            ).first()
            if existing_order:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(bill)
                session.commit()
                session.refresh(bill)
                return bill
    except IntegrityError as e:
        # 输出详细错误信息
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail="Integrity error occurred.")
    except Exception as e:
        # 捕获其他异常
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    

# 20250814 进行功能开发，增加账务修正。
# 工户余额：2327，数据库总额：14892，技师发放金额：9807
# 增加修正值：2758

# 交税百分比
tax_rate = 0.06
# 提现手续费
withdraw_fee = 5
# 20250814钱有账务信息没有保存到bill 表单中。
balance_adjustment_0814 = 0
# balance_adjustment_0814 = 2758

@router.get("/city/statistics")
async def statisticsnew(
    city: Optional[str] = None,
    session: Session = Depends(get_session)
    ):
    logger.info('------------查询平台账户信息-----------------',city)
    total_query = select(
            func.sum(T_Bill.amount).label('total_amount'),
            func.sum(T_Bill.tech_income).label('total_tech_income'),
            func.sum(T_Bill.tax).label('total_tax'),
        )
    # 如果 city 参数存在，添加过滤条件
    if city:
        total_query = total_query.where(T_Bill.work_city == city)
    # 执行查询
    total_result = session.exec(total_query).first()
    totol_income = total_result.total_amount - total_result.total_tech_income - total_result.total_tax
    # logger.info(f"total_result: {total_result}")
    # logger.info(f"totol_income: {totol_income}")
    logger.info('------------查询股东收益（半月）-----------------')
    # 构建查询
    month_query = select(
        func.sum(T_Bill.amount).label('total_amount'),
        func.sum(T_Bill.tech_income).label('total_tech_income'),
        func.sum(T_Bill.tax).label('total_tax'),
    ).where(
        T_Bill.payment_status.isnot(None),
        T_Bill.payment_status != 'completed'  # 注意：使用 <= 确保包括结束日期
    )
    if city:
        month_query = month_query.where(T_Bill.work_city == city)
    month_total_result = session.exec(month_query).first()
    # month_totol_income = month_total_result.total_amount - month_total_result.total_tech_income - month_total_result.total_tax
    # 计算总收入，确保即使结果为 None 也返回 0
    month_total_income = (
        (month_total_result.total_amount if month_total_result.total_amount is not None else 0) -
        (month_total_result.total_tech_income if month_total_result.total_tech_income is not None else 0) -
        (month_total_result.total_tax if month_total_result.total_tax is not None else 0)
    )
    # logger.info(f"month_total_result: {month_total_result}")
    # logger.info(f"month_total_income: {month_total_income}")
    # logger.info('------------查询技师一期收益（周五：0:00～周四23:59:59）-----------------')
    # 查询本周的总和 
    today = datetime.now()
    # 计算起始和结束日期
    if today.weekday() < 5:  # 如果今天是周一到周四
        start_of_week = today - timedelta(days=(today.weekday() + 2))  # 上周五
    else:  # 如果今天是周五到周日
        start_of_week = today - timedelta(days=(today.weekday() - 4))  # 本周五
    # 设置开始和结束时间为0:00
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7)  # 下周五0:00
    week_query =  select(
            func.sum(T_Bill.amount).label('total_amount'),
            func.sum(T_Bill.tech_income).label('total_tech_income'),
        ).where(
            T_Bill.time_stamp >= start_of_week,
            T_Bill.time_stamp < end_of_week
        )
        
    # 如果 city 参数存在，添加过滤条件
    if city:
        week_query = week_query.where(T_Bill.work_city == city)
    # 执行查询
    week_total_result = session.exec(week_query).first()
    # logger.info(f"week_total_result, {week_total_result}")
    # logger.info('------------查看账单-----------------')
    query = select(T_Bill,T_Order,T_Tech_User.user_nickname.label('actual_user_nickname')).outerjoin(T_Order, T_Bill.order_id == T_Order.order_id).outerjoin(T_Tech_User, T_Order.actual_tech_openid == T_Tech_User.openid)

    if city:
        query = query.where(T_Bill.work_city == city)
    query = query.order_by(T_Bill.order_id.desc())
    bill_results = session.exec(query).all()
    bill_results_list = [
        {
            "bill_id": bill.bill_id,  
            "amount": bill.amount,  
            "tech_income": bill.tech_income,  
            "travel_cost": bill.travel_cost,  
            "tax": bill.tax,  
            "sumincome": bill.amount - bill.tech_income - bill.tax,
            "openid": bill.openid,  
            "user_nickname": bill.user_nickname,  
            "actual_user_nickname":actual_user_nickname,
            "ratio": bill.ratio,  
            "order_id": bill.order_id,  
            "work_city": bill.work_city,  
            "withdrawed": bill.withdrawed,  
            "payment_status": bill.payment_status or "",  
            "time_stamp": bill.time_stamp.isoformat(),  
            "service_time": T_Order.service_time
            # 添加其他需要的属性
        }
        for bill, T_Order, actual_user_nickname in bill_results
    ]
    return {
        "totalsum": total_result.total_amount,   # 总金额
        "totolincome": totol_income, # 已支付股东
        "totalpaid": total_result.total_tech_income, # 已支付技师
        "totaltax": total_result.total_tax, # 已支付税收
        "weektotalstarttime": start_of_week,  # 本期开始时间
        "weektotalendtime": end_of_week,  # 本期结束时间
        "weektotalsum": week_total_result.total_amount,  # 本周营业额
        "weeksumtechincome": week_total_result.total_tech_income,  # 本期技师收益
        "halfmonthsumamount": getattr(month_total_result, 'total_amount', 0) or 0 ,  # 半月总收入
        "halfmonthsumtechincome": getattr(month_total_result, 'total_tech_income', 0) or 0 ,  # 半月技师收益
        "halfmonthsumtax": getattr(month_total_result, 'total_tax', 0) or 0 ,  # 半月税收
        "halfmonthsumincome": month_total_income,  # 半月净利润
        "bill_results": bill_results_list
    }

@router.post("/modify")
async def update_bill(bill_id: int, newBill: T_Bill):
    with Session(engine) as session:
        statement = select(T_Bill).where(T_Bill.bill_id == bill_id)
        result = session.exec(statement)
        bill = result.one()
        bill.amount = newBill.amount
        bill.openid = newBill.openid
        bill.user_nickname = newBill.user_nickname
        bill.ratio = newBill.ratio
        bill.order_id = newBill.order_id
        bill.work_city = newBill.work_city
        bill.payment_status = newBill.payment_status
        bill.time_stamp = datetime.now()
        session.add(bill)
        session.commit()
        session.refresh(bill)
        return bill


@router.post("/del/{bill_id}")
async def delete_bill(bill_id: int):
    with Session(engine) as session:
        statement = select(T_Bill).where(T_Bill.bill_id == bill_id)
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}
