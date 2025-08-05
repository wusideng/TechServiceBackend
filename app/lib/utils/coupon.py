from typing import List

from app.model.t_coupon import T_Coupon


def group_coupons(compensate_coupons: List[T_Coupon]):
    coupon_stats = {}
    for coupon in compensate_coupons:
        coupon_value = coupon.amount  # amount字段存储的是优惠券面值
        if coupon_value in coupon_stats:
            coupon_stats[coupon_value] += 1
        else:
            coupon_stats[coupon_value] = 1

    # 转换为所需格式
    compensate_coupons_result = [
        {"coupon_value": coupon_value, "amount": amount}
        for coupon_value, amount in coupon_stats.items()
    ]
    return compensate_coupons_result
