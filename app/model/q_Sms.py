from typing import Optional
from pydantic import BaseModel


class InviteHerRequest(BaseModel):
    client_openid: str
    tech_openid: str


class SendSmsVerificationCodeRequest(BaseModel):
    phone: str
    user_openid: str


class UpdateUserPhoneRequest(BaseModel):
    user_openid: str
    phone: str
    code: Optional[str] = None
