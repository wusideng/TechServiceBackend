from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import desc


class T_Wechat_Events(SQLModel, table=True):
    """微信推送事件，如关注，扫码关注，关注后又扫码等"""

    __tablename__ = "t_wechat_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_openid: str = Field(foreign_key="t_client_user.openid")
    event_type: str = Field(nullable=False)
    scene_str: Optional[str] = Field(nullable=True)
    create_time: datetime = Field(default_factory=datetime.now)


# event_type:scan_and_follow, scan_after_follow, normal_follow
