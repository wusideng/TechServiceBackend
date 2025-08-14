#  账单信息
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import and_, desc, exists, or_
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

import traceback

from app.core.database import engine, get_session
from app.model.t_bill import T_Bill
from app.model.t_order import T_Order
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
async def statistics(
    city: Optional[str] = None,
    session: Session = Depends(get_session)
    ):
    # 查询总金额
    logger.info('------------查询平台账户信息-----------------')
    totalsum = float(session.exec(text("SELECT SUM(amount) FROM t_bill WHERE work_city = '杭州市'")).scalar() or 0)
    logger.info(f"总金额, {totalsum}")
    # 查询已支付技师（已支付 = 技师收益+手续费）
        # 手续费
    totalcount = session.exec(text("SELECT count(*) FROM t_bill WHERE work_city = '杭州市' AND payment_status = 'completed'")).scalar()
    total_withdraw_fee = totalcount * withdraw_fee
        # 技师收益
    tech_completed = float(session.exec(text("SELECT SUM(tech_income) FROM t_bill WHERE work_city = '杭州市' AND payment_status = 'completed'")).scalar() or 0)
    totalpaid = tech_completed + total_withdraw_fee
    logger.info(f"已发放技师收益：{totalpaid}")
    # 已支付股东
    totolincome = totalsum - totalsum * 0.06 - totalpaid + balance_adjustment_0814
    logger.info(totolincome)
    # 银行卡账户余额（总金额-已支付技师-已支付股东）
    card_balance = totalsum - totalpaid - totolincome
    logger.info(card_balance)
    
    # 本周收益,按照城市查看
    currentotalsum = session.exec(text("SELECT SUM(amount) FROM t_bill WHERE work_city = '杭州市'  AND time_stamp >= DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()), 0)")).scalar()
    
    bill_statement = select(T_Bill).order_by(T_Bill.time_stamp.desc())
    bill_result = session.exec(bill_statement).all()
    # return bill_result
    return {
        "totalsum": totalsum,   # 总金额
        "totolincome": round(totolincome,2), # 已支付股东
        "totalpaid": round(totalpaid), # 已支付技师
        "card_balance": round(card_balance), # 银行卡账户余额
        "currentotalsum": currentotalsum,  # 本周收益
        "bill_result": bill_result
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
