# 服务端
## 支持 客户端，技师端，管理端，三套前端工程，共享数据库；
test
 git@github.com:wusideng/TechFrontService.git (push)
find . -name "._*" -print
find . -name "._*" -delete
find . -name "*.pyc" -delete

git rm --cached .gitignore


本地调制：
http://127.0.0.1:8000/docs
服务器地址：
http://visualstreet.cn:8000/docs

调试模式 python main.py --reload

GIT 
  代码提交：
    添加所有文件：
    git add .
    执行第一次提交，并添加提交信息：
    git commit -m "初次提交"
    如果你还没有将本地仓库与远程仓库关联，可以使用以下命令添加远程仓库：
    git remote add origin <远程仓库URL>
    如果你想将第一次提交推送到远程仓库，使用以下命令：
    git push -u origin main

  你可以通过以下命令检查哪些文件将被忽略：
  bash
  git check-ignore -v *
  git rm --cached .gitignore


  检查远程连接：
  git remote -v
  更改远程连接：
  git remote set-url origin git@github.com:wusideng/homeServiceBackend.git

find . -name "._*" -print
find . -name "._*" -delete

数据示例：
wx_UserInfo
{
  "openid": "oK9p06eiEk0jWNvowVjb5lGlkocM",
  "nickname": "xyz",
  "sex": 0,
  "language": "",
  "city": "",
  "province": "",
  "country": "",
  "headimgurl": "https://thirdwx.qlogo.cn/mmopen/vi_32/Q0j4TwGTfTKbWwpicJhyAcYbb40Yg1lboeYv9cb2pxcjVxWzECMGyAlUxiaAKgD6iaoMVBuhvdgvZmueabJBl5RuQ/132",
  "privilege": []
}
wx_jsapi_ticket
{
  "appId": "wxfa6035d95514257e",
  "timestamp": 1733890194,
  "nonceStr": "xcmm7znp35gwpob4",
  "signature": "8af306359f2bed65615abc429c28260b44a9e9ba"
}


windowServer2008R2 

pip3 install alibabacloud_dysmsapi20170525==3.1.1
https://next.api.aliyun.com/api-tools/sdk/Dysmsapi?version=2017-05-25&language=python-tea&tab=primer-doc

如遇到找不到dll异常，则安装如下插件
pip3 install cryptography==36.0.1  

pip3 install pytz

access_token 
https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wxfa6035d95514257e&secret=372414c4d175f744237633bfb2432ef8

获取位置信息
iphone 13
获取位置失败，请检查权限设置
{"errMsg": "getLocation: invalid signature"}
realAuthUrl:["http://visualstreet.cn/devtech/?code=091XAdml2xSTGe4DaHnl2Xyy8G0XAdmb&state=ivirs"]

华为
{"errMsg": "getLocation:invalid signature"}
获取位置失败，请检查权限设置


# 版本发布：
core/config.py
  根据不同环境修改
  settings = Settings()
  settings = SettingsDev()


项目运行：
python 环境：python3.8.8
本地开发：
pip install -r requirements.txt
config.py is_dev="true"
python main.py
生产环境：
config.py is_dev="false"
pip install -r requirements.txt
python main.py



ngrok固定域名：guppy

ngrok config add-authtoken 2eiQtlUs243jVhe3EoUpzDSjd0i_7bzhwuvx271mXQoVAsxyb
ngrok http --url=loyal-globally-guppy.ngrok-free.app 8000
