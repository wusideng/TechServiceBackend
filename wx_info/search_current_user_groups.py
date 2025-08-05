import requests
import json
from get_access_token import get_access_token


def get_wechat_tags(access_token):
    """
    获取微信公众号中的所有用户标签

    参数:
    access_token (str): 微信公众号的访问令牌

    返回:
    dict: 包含标签信息的字典
    """
    # 查询标签的API URL
    url = f"https://api.weixin.qq.com/cgi-bin/tags/get?access_token={access_token}"

    try:
        # 发送GET请求
        response = requests.get(url)
        result = response.json()

        # 检查是否请求成功
        if "errcode" in result and result["errcode"] != 0:
            print(f"错误: {result['errmsg']}, 错误代码: {result['errcode']}")
            return None

        # 打印标签信息
        print("所有标签及ID:")
        for tag in result.get("tags", []):
            print(
                f"标签名: {tag['name']}, 标签ID: {tag['id']}, 粉丝数: {tag.get('count', 0)}"
            )

        return result
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None


def find_tag_id_by_name(tags_result, tag_name):
    """
    根据标签名查找标签ID

    参数:
    tags_result (dict): 包含标签信息的字典
    tag_name (str): 要查找的标签名

    返回:
    int: 标签ID，如果未找到则返回None
    """
    if not tags_result or "tags" not in tags_result:
        return None

    for tag in tags_result["tags"]:
        if tag["name"] == tag_name:
            return tag["id"]

    return None


def main():
    access_token = get_access_token()
    if not access_token:
        return

    # 获取所有标签
    tags_result = get_wechat_tags(access_token)
    if not tags_result:
        return
    print(tags_result)


if __name__ == "__main__":
    tag_ids = main()

    # 如果需要，可以将标签ID保存到配置文件
    if tag_ids and tag_ids["test_env_tag_id"] and tag_ids["area_mgmt_tag_id"]:
        with open("tag_ids.json", "w") as f:
            json.dump(tag_ids, f)
        print("\n标签ID已保存到tag_ids.json文件")
