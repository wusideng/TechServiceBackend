#  产品信息
import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import Session, select
from sqlalchemy import func
from app.model.t_order_product import T_Order_Product
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.lib.utils.upload import upload_file_to_cdn
from app.model.t_product import T_Product

router = APIRouter(
    prefix="/products",
    tags=["products"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_products(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        # 批量查询所有产品的订单数量
        order_counts = session.exec(
            select(
                T_Order_Product.product_id,
                func.count(T_Order_Product.order_p_id).label("order_count"),
            ).group_by(T_Order_Product.product_id)
        ).all()
        order_counts_dict = dict(order_counts)

        # 查询所有产品并关联订单数量
        products = session.exec(
            select(T_Product).order_by(T_Product.price_current)
        ).all()

        result = [
            {
                **product.model_dump(),
                "order_count": order_counts_dict.get(product.product_id, 0),
            }
            for product in products
        ]

        return {
            "data": result,
        }


@router.get("/{product_id}")
async def read_product(product_id: str):
    with Session(engine) as session:
        statement = select(T_Product).where(T_Product.product_id == product_id)
        results = session.exec(statement)
        return results.first()


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
                session.refresh(product)
                return {"msg": "create sucess", "data": product}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/modify/")
async def update_product(product_id: int, newProduct: T_Product):
    with Session(engine) as session:
        statement = select(T_Product).where(T_Product.product_id == product_id)
        result = session.exec(statement)
        product = result.one()
        product.product_name = newProduct.product_name
        product.price_old = newProduct.price_old
        product.introduction = newProduct.introduction
        product.consumables = newProduct.consumables
        product.promotion = newProduct.promotion
        product.price_current = newProduct.price_current
        product.duration = newProduct.duration
        product.body_parts = newProduct.body_parts
        product.contraindication = newProduct.contraindication
        session.add(product)
        session.commit()
        session.refresh(product)
        return product


@router.post("/photoDemo")
async def create_p_photo(photo_intro: UploadFile = File(...)):
    # print("photo_intro:", photo_intro)
    # 保存上传的照片
    photo_filename = "Prod_" + photo_intro.filename
    upload_cdn_folder_path = "uploads"
    await upload_file_to_cdn(photo_intro, upload_cdn_folder_path, photo_filename)
    # photo_path = os.path.join(settings.PRODUCT_PICTURES, "Prod_" + photo_intro.filename)
    # with open(photo_path, "wb") as buffer:
    #     buffer.write(await photo_intro.read())


@router.post("/photo")
async def update_product_photo(
    product_id: int,
    photo_intro: UploadFile = File(None),
    photo_detail1: UploadFile = File(None),
    photo_detail2: UploadFile = File(None),
    photo_detail3: UploadFile = File(None),
):
    with Session(engine) as session:
        statement = select(T_Product).where(T_Product.product_id == product_id)
        result = session.exec(statement)
        if not result.first():
            raise HTTPException(status_code=400, detail="the product not exists.")
        else:
            # 保存上传的照片
            statement = select(T_Product).where(T_Product.product_id == product_id)
            result = session.exec(statement)
            product = result.first()
            if photo_intro:
                cdn_path = await upload_photo_to_cdn(photo_intro, product_id)
                product.photo_intro = cdn_path
            if photo_detail1:
                cdn_path = await upload_photo_to_cdn(photo_detail1, product_id)
                product.photo_detail1 = cdn_path
            if photo_detail2:
                cdn_path = await upload_photo_to_cdn(photo_detail2, product_id)
                product.photo_detail2 = cdn_path
            if photo_detail3:
                cdn_path = await upload_photo_to_cdn(photo_detail3, product_id)
                product.photo_detail3 = cdn_path
            session.add(product)
            session.commit()
            session.refresh(product)
            return product


@router.put("/")
async def update_product(product_id: int, newProduct: T_Product):
    with Session(engine) as session:
        statement = select(T_Product).where(T_Product.product_id == product_id)
        result = session.exec(statement)
        product = result.one()
        product.product_name = newProduct.product_name
        product.price_old = newProduct.price_old
        product.introduction = newProduct.introduction
        product.consumables = newProduct.consumables
        product.promotion = newProduct.promotion
        product.price_current = newProduct.price_current
        product.duration = newProduct.duration
        product.body_parts = newProduct.body_parts
        product.contraindication = newProduct.contraindication
        session.add(product)
        session.commit()
        session.refresh(product)
        return product


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
        return {"msg": "delete sucess", "data": product}


async def upload_photo_to_cdn(photo: UploadFile, product_id: int):
    photo_filename = "Prod_" + str(product_id) + "_" + photo.filename
    upload_cdn_folder_path = "uploads"
    cdn_path = await upload_file_to_cdn(photo, upload_cdn_folder_path, photo_filename)
    return cdn_path
