#  订单信息
import asyncio
from fastapi import APIRouter

router = APIRouter()

router = APIRouter(
    prefix="/refundAutoFix",
    tags=["refundAutoFix"],
    # dependencies=[Depends(get_sys_token_header)],
    # responses={404: {"description": "Not found"}},
)


# 对数据库中payment_status是退款中的order进行状态轮询
# todo  自动寻找哪些退款状态有问题的订单，并去轮训微信的接口，自动修复状态


@router.post("/")
async def refund_auto_fix_handler(order_id):
    out_refund_no = order_id
    # 尽管我们已经在数据库refunds表中存下了对应的refund_id，但是依然有可能因为网络问题导致没有存下来，所以这里需要再次查询
    refund_id = await get_refund_id_from_out_refund_no(out_refund_no)
    refund_info = None
    while refund_info is None:
        # 根据refund_id获取refund的最新信息
        refund_info = await get_refund_info(out_refund_no)
        if refund_info is None:
            await asyncio.sleep(1800)  # 等待30分钟
    return refund_info


# 根据轮询结果，更新数据库的order，order_status和refunds三张表
def updateDB(order_id, refund_info):
    # 更新数据库
    pass
