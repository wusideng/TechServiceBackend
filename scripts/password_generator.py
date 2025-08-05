import random
import string
import secrets


def generate_strong_password():
    """
    生成一个高安全性的随机密码
    - 长度为16-20个字符
    - 包含大写字母、小写字母、数字和特殊字符
    - 确保每种字符类型至少出现一次
    - 使用cryptographically强壮的随机数生成器
    """
    # 设定密码长度(16-20之间)
    length = secrets.randbelow(5) + 16

    # 确保每种字符类型至少出现一次
    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?/")

    # 计算剩余字符数量
    remaining_length = length - 4

    # 创建完整字符集
    all_chars = (
        string.ascii_lowercase
        + string.ascii_uppercase
        + string.digits
        + "!@#$%^&*()-_=+[]{}|;:,.<>?/"
    )

    # 生成剩余随机字符
    remaining_chars = "".join(
        secrets.choice(all_chars) for _ in range(remaining_length)
    )

    # 合并所有字符
    password_chars = lowercase + uppercase + digit + special + remaining_chars

    # 打乱字符顺序
    password_list = list(password_chars)
    secrets.SystemRandom().shuffle(password_list)

    # 返回最终密码
    return "".join(password_list)


# 使用示例
if __name__ == "__main__":
    print("=== 高安全性密码生成器 ===")
    password = generate_strong_password()
    print(f"生成的密码: {password}")
    print(f"密码长度: {len(password)}位")
    print("已确保包含大写字母、小写字母、数字和特殊字符")
