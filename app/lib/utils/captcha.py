from captcha.image import ImageCaptcha
import random
import string
import io


# 生成验证码
def generate_captcha_text(length=5):
    # 使用混合大小写字母和数字，但排除容易混淆的字符
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    for c in "oO0iIl1":  # 移除容易混淆的字符
        chars = chars.replace(c, "")

    return "".join(random.choice(chars) for _ in range(length))


def generate_captcha_image_from_text(captcha_text, width=160, height=40):
    # 创建验证码图像 - 使用默认参数，不访问内部属性
    image = ImageCaptcha(width=width, height=height)
    # 生成图像并应用干扰
    img_data = io.BytesIO()
    # 生成验证码图片 - captcha库会自动添加一些干扰
    img = image.generate_image(captcha_text)
    # 保存为PNG
    img.save(img_data, format="PNG")
    img_data.seek(0)
    return img_data
