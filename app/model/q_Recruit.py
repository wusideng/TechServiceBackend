from pydantic import BaseModel


class UpdateRecruitRequest(BaseModel):
    id: int
    has_contacted: bool
    remark: str
