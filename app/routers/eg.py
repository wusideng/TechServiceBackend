#  示例
import os
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.model.t_product import T_Product

router = APIRouter(
    prefix="/eg",
    tags=["eg"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_products(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Product)).all()
        total_count = len(total_count)
        statement = (
            select(T_Product)
            .order_by(T_Product.product_id)
            .offset(offset)
            .limit(pageSize)
        )

        products = session.exec(statement).all()
        return {
            "total_count": total_count,
            "products": products,
            "page": pageNum,
            "page_size": pageSize,
            "total_pages": (total_count // pageSize)
            + (1 if total_count % pageSize > 0 else 0),
        }


@router.get("/{product_id}")
async def read_product(product_id: str):
    with Session(engine) as session:
        statement = select(T_Product).where(T_Product.product_id == product_id)
        results = session.exec(statement)
        return {"code": 200, "data": results.first()}


@router.post("/")
async def create_product(product: T_Product):
    try:
        with Session(engine) as session:
            existing_product = session.exec(
                select(T_Product).where(T_Product.product_id == product.product_id)
            ).first()
            if existing_product:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(product)
                session.commit()
                return {"code": 200, "data": "success"}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_product(product_id: int, newProduct: T_Product):
    with Session(engine) as session:
        statement = select(T_Product).where(T_Product.product_id == product_id)
        result = session.exec(statement)
        product = result.one()
        product.product_name = newProduct.product_name
        session.add(product)
        session.commit()
        return {"code": 200, "data": product}


@router.post("/del/{product_id}")
async def delete_product(product_id: int):
    with Session(engine) as session:
        statement = select(T_Product).where(T_Product.product_id == product_id)
        results = session.exec(statement)
        product = results.first()
        if not product:
            return {"code": 200, "data": "there's no product"}
        session.delete(product)
        session.commit()
        return {"code": 200, "msg": "delete sucess", "data": product}
