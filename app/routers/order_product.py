#  订单信息

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.model.t_order_product import T_Order_Product

router = APIRouter()

router = APIRouter(
    prefix="/ordersProd",
    tags=["ordersProd"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_orders(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Order_Product)).all()
        total_count = len(total_count)
        statement = (
            select(T_Order_Product)
            .order_by(T_Order_Product.order_p_id)
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


@router.get("/{order_p_id}")
async def read_order(order_p_id: str):
    with Session(engine) as session:
        statement = select(T_Order_Product).where(
            T_Order_Product.order_p_id == order_p_id
        )
        results = session.exec(statement)
        return results.first()


@router.post("/")
async def create_order(order_prod: T_Order_Product):
    try:
        with Session(engine) as session:
            existing_order = session.exec(
                select(T_Order_Product).where(
                    T_Order_Product.order_p_id == order_prod.order_p_id
                )
            ).first()
            if existing_order:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(order_prod)
                session.commit()
                session.refresh(order_prod)
                return {"msg": "create sucess", "data": order_prod}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_order(order_p_id: int, newOrderProd: T_Order_Product):
    with Session(engine) as session:
        statement = select(T_Order_Product).where(
            T_Order_Product.order_p_id == order_p_id
        )
        result = session.exec(statement)
        order = result.one()
        order.product_id = newOrderProd.product_id
        order.product_name = newOrderProd.product_name
        session.add(order)
        session.commit()
        session.refresh(order)
        return order


@router.post("/del/{order_p_id}")
async def delete_order(order_p_id: int):
    with Session(engine) as session:
        statement = select(T_Order_Product).where(
            T_Order_Product.order_p_id == order_p_id
        )
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}
