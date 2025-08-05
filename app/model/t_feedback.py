from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional


class T_Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_openid: str
    content: str
    contact_phone: Optional[str]
    user_phone_registered: Optional[str]
    # 0:未处理 1:处理中 2:已处理
    status: int = Field(default=0)
    create_time: Optional[datetime] = Field(default_factory=datetime.now)  # 创建时间
    update_time: Optional[datetime] = Field(default_factory=datetime.now)  # 更新时间
    processed_by: Optional[str]
    process_result: Optional[str]
    img_url1: Optional[str]
    img_url2: Optional[str]
    img_url3: Optional[str]
    reply: Optional[str]
    reply_at: Optional[datetime]
