#  订单信息

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.model.t_tech_user_product import T_Tech_User_Product
from app.model.t_product import T_Product
from app.model.t_tech_user import T_Tech_User
from app.model.q_UserProductsUpdate import UserProductsUpdate

router = APIRouter(
    prefix="/techUserProduct",
    tags=["techUserProduct"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_products(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Tech_User_Product)).all()
        total_count = len(total_count)
        statement = (
            select(T_Tech_User_Product)
            .order_by(T_Tech_User_Product.user_product_id)
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
async def create_product(techUserProduct: T_Tech_User_Product):
    try:
        with Session(engine) as session:
            existing_product = session.exec(
                select(T_Tech_User_Product).where(
                    T_Tech_User_Product.user_product_id
                    == techUserProduct.user_product_id
                )
            ).first()
            if existing_product:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(techUserProduct)
                session.commit()
                session.refresh(techUserProduct)
                return {"msg": "create sucess", "data": techUserProduct}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/del/{user_product_id}")
async def delete_product(user_product_id: int):
    with Session(engine) as session:
        statement = select(T_Tech_User_Product).where(
            T_Tech_User_Product.user_product_id == user_product_id
        )
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}


# 技师关联产品信息查看
@router.get("/{user_id}/products")
def get_user_products(user_id: int):
    with Session(engine) as session:
        statement = (
            select(T_Product)
            .select_from(T_Tech_User_Product)
            .join(T_Product, T_Tech_User_Product.product_id == T_Product.product_id)
            .where(T_Tech_User_Product.user_id == user_id)
            .order_by(T_Product.price_current)
        )
    user_products = session.exec(statement).all()
    return user_products


# 技师关联产品信息查看
@router.get("/{user_id}/products")
def get_user_products(user_id: int):
    with Session(engine) as session:
        statement = (
            select(T_Product)
            .join(T_Tech_User_Product)
            .where(T_Tech_User_Product.user_id == user_id)
        )
        statement = (
            select(T_Product)
            .select_from(T_Tech_User_Product)
            .join(T_Product, T_Tech_User_Product.product_id == T_Product.product_id)
            .where(T_Tech_User_Product.user_id == user_id)
            .order_by(T_Product.price_current)
        )
    user_products = session.exec(statement).all()
    return user_products


@router.post("/{user_id}/products/update")
def update_user_products(user_id: int, user_products: UserProductsUpdate):
    with Session(engine) as session:
        # 查找用户是否存在
        user = session.get(T_Tech_User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        # 获取当前用户的所有产品
        current_user_products = select(T_Tech_User_Product).where(
            T_Tech_User_Product.user_id == user_id
        )
        current_user_products = session.exec(current_user_products)
        current_user_products = current_user_products.all()
        current_product_ids = {up.product_id for up in current_user_products}

        # 新增或保持的产品 ID
        new_product_ids = set(user_products.product_ids)

        # 添加新的产品关联
        for product_id in new_product_ids:
            if product_id not in current_product_ids:
                # 查找产品是否存在
                product = session.get(T_Product, product_id)
                if product is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Product with id {product_id} not found.",
                    )
                # 创建新的用户产品关联
                new_user_product = T_Tech_User_Product(
                    user_id=user_id,
                    product_id=product_id,
                )
                session.add(new_user_product)
                session.commit()

        # 删除不在更新列表中的产品
        for product_id in current_product_ids:
            if product_id not in new_product_ids:
                # 查找并删除
                user_product = (
                    session.query(T_Tech_User_Product)
                    .filter_by(user_id=user_id, product_id=product_id)
                    .first()
                )
                if user_product:
                    session.delete(user_product)
                session.commit()
        return {"message": "Products updated successfully"}
