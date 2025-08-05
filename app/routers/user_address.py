from fastapi import APIRouter, HTTPException, Request, Depends
from sqlmodel import Session, select, update, desc

from app.core.database import get_session
from app.model.t_user_addresses import UserAddress
from logger import logger

router = APIRouter(
    prefix="/user",
    tags=["userAddress"],
)


@router.get("/addresses")
async def get_user_addresses(openid: str, session: Session = Depends(get_session)):
    """获取用户地址列表"""
    try:
        statement = (
            select(UserAddress)
            .where(UserAddress.openid == openid)
            .order_by(desc(UserAddress.create_time))
        )
        addresses = session.exec(statement).all()
        return addresses
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/addresses")
async def add_user_address(
    address: UserAddress, session: Session = Depends(get_session)
):
    """添加新地址"""
    try:
        # 创建新地址
        # 如果设置为默认地址，先将其他地址设为非默认
        if address.is_default and address.openid:
            statement = select(UserAddress).where(
                UserAddress.openid == address.openid,
                UserAddress.is_default == True,
            )
            default_addresses = session.exec(statement).all()
            for addr in default_addresses:
                addr.is_default = False
                session.add(addr)

        session.add(address)
        session.commit()
        session.refresh(address)

        return address
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/addresses/{address_id}")
async def update_user_address(
    address_id: int,
    address_update: UserAddress,
    session: Session = Depends(get_session),
):
    """更新地址"""
    try:
        # 获取要更新的地址
        statement = select(UserAddress).where(UserAddress.id == address_id)
        address = session.exec(statement).first()

        if not address:
            raise HTTPException(status_code=404, detail="地址不存在")

        # 如果设置为默认地址，先将其他地址设为非默认
        if address_update.is_default and address.openid:
            default_statement = select(UserAddress).where(
                UserAddress.openid == address.openid,
                UserAddress.is_default == True,
                UserAddress.id != address_id,
            )
            default_addresses = session.exec(default_statement).all()
            for addr in default_addresses:
                addr.is_default = False
        for key, value in address_update.model_dump(exclude={"id"}).items():
            if key != "create_time":
                setattr(address, key, value)
        session.commit()
        session.refresh(address)

        return address
    except HTTPException as e:
        logger.error(e)
        raise e
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/addresses/default")
async def get_user_default_address(
    openid: str, session: Session = Depends(get_session)
):
    """获取用户默认地址，如果没有默认地址则返回最近添加的地址"""
    try:
        # 先查找默认地址
        default_statement = select(UserAddress).where(
            UserAddress.openid == openid, UserAddress.is_default == True
        )
        default_address = session.exec(default_statement).first()

        if default_address:
            return default_address

        # 如果没有默认地址，获取最近创建的地址
        latest_statement = (
            select(UserAddress)
            .where(UserAddress.openid == openid)
            .order_by(desc(UserAddress.create_time))
        )
        latest_address = session.exec(latest_statement).first()

        if latest_address:
            return latest_address

        # 如果没有任何地址，返回None
        return None
    except HTTPException as e:
        logger.error(e)
        raise e
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/addresses/{address_id}")
async def delete_user_address(address_id: int, session: Session = Depends(get_session)):
    """删除地址"""
    try:
        # 获取要删除的地址
        statement = select(UserAddress).where(UserAddress.id == address_id)
        address = session.exec(statement).first()

        if not address:
            raise HTTPException(status_code=404, detail="地址不存在")

        # 删除地址
        session.delete(address)
        session.commit()

        return {"code": 200, "message": "地址删除成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
