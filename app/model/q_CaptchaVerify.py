from pydantic import BaseModel


class CaptchaVerifyRequest(BaseModel):
    tech_user_id: int
    captcha_text: str
