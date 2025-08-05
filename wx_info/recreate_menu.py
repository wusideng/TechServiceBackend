import requests
import json
from get_access_token import get_access_token

# 标签ID
test_tag_id = 104  # 测试环境组的标签ID
area_tag_id = 103  # 区域管理组的标签ID


def create_wechat_menus(access_token):
    access_token = get_access_token()
    create_menu_url = (
        f"https://api.weixin.qq.com/cgi-bin/menu/create?access_token={access_token}"
    )
    add_conditional_menu_url = f"https://api.weixin.qq.com/cgi-bin/menu/addconditional?access_token={access_token}"
    delete_menu_url = (
        f"https://api.weixin.qq.com/cgi-bin/menu/delete?access_token={access_token}"
    )

    # # 首先删除现有菜单
    # try:
    #     print("正在删除现有菜单...")
    #     response = requests.get(delete_menu_url)
    #     result = response.json()

    #     if result.get("errcode") == 0:
    #         print("现有菜单已成功删除")
    #     else:
    #         print(
    #             f"删除菜单失败: {result.get('errmsg')}, 错误代码: {result.get('errcode')}"
    #         )
    # except Exception as e:
    #     print(f"删除菜单请求失败: {str(e)}")

    # 结果字典
    results = {}

    # 1. 创建基础菜单（所有用户可见）
    base_menu = {
        "button": [
            {
                "type": "view",
                "name": "立即下单",
                "url": "https://visualstreet.cn/prodclient/",
            },
            {
                "type": "view",
                "name": "我要加入",
                "url": "https://visualstreet.cn/prodtech/",
            },
        ]
    }

    try:
        print("正在创建基础菜单...")
        response = requests.post(
            create_menu_url,
            data=json.dumps(base_menu, ensure_ascii=False).encode("utf-8"),
        )
        result = response.json()

        if result.get("errcode") == 0:
            print("基础菜单创建成功")
        else:
            print(
                f"基础菜单创建失败: {result.get('errmsg')}, 错误代码: {result.get('errcode')}"
            )

        results["base_menu"] = result
    except Exception as e:
        print(f"创建基础菜单请求失败: {str(e)}")
        results["base_menu"] = {"error": str(e)}

    # 2. 创建测试环境组的个性化菜单
    test_menu = {
        "button": [
            {
                "type": "view",
                "name": "立即下单",
                "url": "https://visualstreet.cn/prodclient/",
            },
            {
                "type": "view",
                "name": "我要加入",
                "url": "https://visualstreet.cn/prodtech/",
            },
            {
                "name": "测试环境",
                "sub_button": [
                    {
                        "type": "view",
                        "name": "技师端",
                        "url": "https://visualstreet.cn/devtech/",
                    },
                    {
                        "type": "view",
                        "name": "客户端",
                        "url": "https://visualstreet.cn/devclient/",
                    },
                    {
                        "type": "view",
                        "name": "管理后台",
                        "url": "https://visualstreet.cn/devservice/",
                    },
                    {
                        "type": "view",
                        "name": "管理后台_区域管理",
                        "url": "https://visualstreet.cn/prodservice/",
                    },
                    {
                        "type": "view",
                        "name": "城市管理_区域管理",
                        "url": "https://visualstreet.cn/cityclient/",
                    },
                ],
            },
        ],
        "matchrule": {"tag_id": str(test_tag_id)},
    }

    try:
        print("正在创建测试环境组个性化菜单...")
        response = requests.post(
            add_conditional_menu_url,
            data=json.dumps(test_menu, ensure_ascii=False).encode("utf-8"),
        )
        result = response.json()

        if "menuid" in result:
            print(f"测试环境组个性化菜单创建成功，菜单ID: {result['menuid']}")
        else:
            print(
                f"测试环境组个性化菜单创建失败: {result.get('errmsg')}, 错误代码: {result.get('errcode')}"
            )

        results["test_menu"] = result
    except Exception as e:
        print(f"创建测试环境组个性化菜单请求失败: {str(e)}")
        results["test_menu"] = {"error": str(e)}

    # 3. 创建区域管理组的个性化菜单
    area_menu = {
        "button": [
            {
                "type": "view",
                "name": "立即下单",
                "url": "https://visualstreet.cn/prodclient/",
            },
            {
                "type": "view",
                "name": "我要加入",
                "url": "https://visualstreet.cn/prodtech/",
            },
            {
                "name": "区域管理",
                "sub_button": [
                    {
                        "type": "view",
                        "name": "管理后台",
                        "url": "https://visualstreet.cn/prodservice/",
                    },
                    {
                        "type": "view",
                        "name": "城市管理",
                        "url": "https://visualstreet.cn/cityclient/",
                    },
                    {
                        "type": "view",
                        "name": "保洁客户端",
                        "url": "http://visualstreet.cn/prodclean/",
                    },
                ],
            },
        ],
        "matchrule": {"tag_id": str(area_tag_id)},
    }

    try:
        print("正在创建区域管理组个性化菜单...")
        response = requests.post(
            add_conditional_menu_url,
            data=json.dumps(area_menu, ensure_ascii=False).encode("utf-8"),
        )
        result = response.json()

        if "menuid" in result:
            print(f"区域管理组个性化菜单创建成功，菜单ID: {result['menuid']}")
        else:
            print(
                f"区域管理组个性化菜单创建失败: {result.get('errmsg')}, 错误代码: {result.get('errcode')}"
            )

        results["area_menu"] = result
    except Exception as e:
        print(f"创建区域管理组个性化菜单请求失败: {str(e)}")
        results["area_menu"] = {"error": str(e)}

    return results


def main():

    # 如果已有access_token，可以直接使用
    # access_token = "你的access_token"

    # 获取access_token
    access_token = get_access_token()
    if not access_token:
        print("获取access_token失败，无法继续创建菜单")
        return

    # 创建菜单
    results = create_wechat_menus(access_token)

    # 输出最终结果
    print("\n菜单创建结果摘要:")
    for menu_type, result in results.items():
        if isinstance(result, dict) and "error" in result:
            status = "失败"
        elif menu_type == "base_menu" and result.get("errcode") == 0:
            status = "成功"
        elif menu_type != "base_menu" and "menuid" in result:
            status = "成功"
        else:
            status = "失败"

        print(f"{menu_type}: {status}")


if __name__ == "__main__":
    main()
