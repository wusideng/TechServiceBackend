worker_num = 1

# alibaba
db_user = "sa"
db_password = "H3E7?j.4F<^j_qP%37FV"
db_host = "120.26.38.176:49471"
port = 49471

# tencent
# db_user = "sa"
# db_password = "cldera.com2023"
# db_host = "101.42.110.185:1433"
# port = 1433

product_pictures = "./uploads"
order_pictures = "./uploads"
server_files = "cdn/"
mch_id = "1704709597"
device_info = "WEB"
weixin_pay = "https://api.mch.weixin.qq.com/pay/unifiedorder"
key = "mo8iop4ubyun0u5hesxkotsua1os6uat"
app_id = "wxfa6035d95514257e"
app_secret = "372414c4d175f744237633bfb2432ef8"
wx_cert_path = "c:\\workspace\\cert\\apiclient_cert.pem"
wx_key_path = "c:\\workspace\\cert\\apiclient_key.pem"
wx_cert = "c:\\workspace\\cert\\apiclient_cert.p12"
pay_test_openids = [
    "oK9p06eiEk0jWNvowVjb5lGlkocM",
    "oK9p06S43s67ui0VxR3-h3REu0VY",
    "oK9p06UX2a02_b9Cn4W7cfoWjE3c",
    # cheng-dianxin
    "oK9p06dxisAkfHLgD-vZIUFmypAg",
]
# 订单支付超时时间
order_pay_timeout = 1800
cdn_info = {
    # # 尚达元CDN
    # "access_key": "B0N2T8EneCYnW6BswNSJmYkWUXJVPtobHPnxSuFL",
    # "secret_key": "r9DGBnaxxLVpik8YgIVvuNgIm_5is9Dq5taL6egF",
    # "bucket": "shangdayuan",
    # # 姜程退出后新申请的CDN
    "access_key": '7NaZvZKm2wMZ80DbxrbXhq6GyKOir7qhznodO9_X',
    "secret_key": 'UVRTUZHFbjvplwTQBbnIjphysOkjwNH9OYg9gTHk',
    "bucket": 'visualstreet'
}



# 订单通知管理员的手机号
adminList = [18010260892, 18996531158]

static_url = "https://sdy.visualstreet.cn"
# 用于接收微信通知，如扫描二维码等
WECHAT_TOKEN = "ROE2V6adoxvseC1KIYBoIaVa75b"
WECHAT_EncodingAESKey = "7UiErBVeNhiRetfyDcADVLzvANvF3Xq1Nq6ZWulLPVy"

# local
is_dev = True
db_name = "home_massage_prod"
# db_name = "home_massage_dev"
server_port = 8000
product_base = "http://127.0.0.1:8000"
enable_pay_test = True


# devconfig
# is_dev = False
# db_name = "home_massage_dev"
# server_port = 8001
# product_base = "https://visualstreet.cn/apidev"
# enable_pay_test = True

##prodconfig
# is_dev = False
# db_name = "home_massage_prod"
# server_port = 8000
# product_base = "https://visualstreet.cn/api"
# enable_pay_test = False


# product_base = "http://visualstreet.cn:8001"
