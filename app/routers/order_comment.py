#  订单信息

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.core.database import engine
from app.model.t_order_comment import T_Order_Comment
from app.model.t_order import T_Order
from app.model.q_OrderCreate import AddFackCommentRequest


router = APIRouter(
    prefix="/ordersComment",
    tags=["ordersComment"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_comments(pageNum: int = 0, pageSize: int = 10):
    with Session(engine) as session:
        offset = pageNum * pageSize
        total_count = session.exec(select(T_Order_Comment)).all()
        total_count = len(total_count)
        statement = (
            select(T_Order_Comment)
            .order_by(T_Order_Comment.order_comment_id)
            .offset(offset)
            .limit(pageSize)
        )
        comments = session.exec(statement).all()
        return {
            "total_count": total_count,
            "data": comments,
            "page": pageNum,
            "page_size": pageSize,
            "total_pages": (total_count // pageSize)
            + (1 if total_count % pageSize > 0 else 0),
        }

# tech_id 保存的是技师的 openid
@router.get("/tech/{tech_id}")
async def get_comments_by_techid(tech_id: str):
    with Session(engine) as session:
        statement = (
            select(T_Order_Comment)
            .where(T_Order_Comment.tech_id == tech_id)
            .order_by(T_Order_Comment.client_comment_time)
        )
        comments = session.exec(statement).all()
        return comments


@router.get("/{order_comment_id}")
async def read_comment(order_comment_id: str):
    with Session(engine) as session:
        statement = select(T_Order_Comment).where(
            T_Order_Comment.order_comment_id == order_comment_id
        )
        results = session.exec(statement)
        return results.first()


@router.post("/")
async def create_comment(order_comment: T_Order_Comment):
    try:
        with Session(engine) as session:
            existing_comment = session.exec(
                select(T_Order_Comment).where(
                    T_Order_Comment.order_comment_id == order_comment.order_comment_id
                )
            ).first()
            if existing_comment:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                session.add(order_comment)
                session.commit()
                session.refresh(order_comment)
                return {"msg": "create sucess", "data": order_comment}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


# 客户评论技师调用此接口，一个订单只有一个评论
@router.post("/clientOrder")
async def create_comment_client(order_comment: T_Order_Comment):
    try:
        with Session(engine) as session:
            existing_comment = session.exec(
                select(T_Order_Comment).where(
                    T_Order_Comment.order_comment_id == order_comment.order_comment_id
                )
            ).first()
            if existing_comment:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique field already exists.",
                )
            else:
                order_comment.client_comment_time = datetime.now()
                session.add(order_comment)
                session.commit()
                session.refresh(order_comment)
                return {"msg": "create sucess", "data": order_comment}
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.post("/techOrder")
async def create_comment_tech(order_comment: T_Order_Comment):
    try:
        with Session(engine) as session:
            existing_order = session.exec(
                select(T_Order_Comment).where(
                    T_Order_Comment.order_comment_id == order_comment.order_comment_id
                )
            ).first()
            if existing_order:
                existing_order.tech_comment_time = datetime.now()
                existing_order.tech_comment = order_comment.tech_comment
                existing_order.tech_comment_time = order_comment.tech_comment_time
                existing_order.tech_score_to_client = order_comment.tech_score_to_client
                session.add(existing_order)
                session.commit()
                session.refresh(existing_order)
                return existing_order
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Item with this unique not create.",
                )
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")


@router.put("/")
async def update_order(order_comment_id: int, newOrderProd: T_Order_Comment):
    with Session(engine) as session:
        statement = select(T_Order_Comment).where(
            T_Order_Comment.order_comment_id == order_comment_id
        )
        result = session.exec(statement)
        order = result.one()
        order.order_id = newOrderProd.order_id
        order.client_comment = newOrderProd.client_comment
        order.client_comment_time = newOrderProd.client_comment_time
        order.client_score_to_tech = newOrderProd.client_score_to_tech
        order.tech_comment = newOrderProd.tech_comment
        order.tech_comment_time = newOrderProd.tech_comment_time
        order.tech_score_to_client = newOrderProd.tech_score_to_client
        session.add(order)
        session.commit()
        session.refresh(order)
        return order


@router.post("/del/{order_comment_id}")
async def delete_order(order_comment_id: int):
    with Session(engine) as session:
        statement = select(T_Order_Comment).where(
            T_Order_Comment.order_comment_id == order_comment_id
        )
        results = session.exec(statement)
        order = results.first()
        if not order:
            return {"msg": "there's no order", "data": ""}
        session.delete(order)
        session.commit()
        return {"msg": "delete sucess", "data": order}



# 新增顾客评价技师，生成一条虚拟订单，生成一条评论。返回当前技师的评论列表
@router.post("/clientFake/{tech_openid}")
async def create_fake_comment_client(tech_openid:str, fack_comment_request: AddFackCommentRequest):
    try:
        with Session(engine) as session:
            # 新增一条模拟订单
            new_order = T_Order(
                create_order_time=datetime.now(),
                service_time=datetime.now(),
                service_address = "fake_address",
                service_city = "fake_city",
                service_detail_address = "fake_detail_address",
                travel_distance = 0,
                travel_cost = 0,
                payment_status = "待支付",
                tech_user_id = tech_openid,
                client_user_id = "fake_client_user_id",
                order_cost = 0,
                remark = "无效订单"
            )
            session.add(new_order)
            session.commit()
            session.refresh(new_order)
            # 新增一条评论信息
            new_comment = T_Order_Comment(
                client_openid = "fake_client_user_id",
                order_id = new_order.order_id,
                tech_id = tech_openid,
                client_comment_time = datetime.now(),
                client_comment = fack_comment_request.client_comment,
                client_score_to_tech=fack_comment_request.client_score_to_tech
            )
            session.add(new_comment)
            session.commit()
            session.refresh(new_comment)
            # 返回本技师评论列表
            commentlist = session.exec(select(T_Order_Comment).order_by(desc(T_Order_Comment.order_comment_id))).all()
            return commentlist
    except IntegrityError:
        raise HTTPException(status_code=401, detail="other error.")