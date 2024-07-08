import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class UserActionCreateBody(BaseModel):
    coproductionprocess_id:  Optional[uuid.UUID]
    task_id:  Optional[uuid.UUID]
    asset_id:  Optional[uuid.UUID]
    path: str
    data: Optional[dict]
    section: Optional[str]
    action: str


class UserActionCreate(UserActionCreateBody):
    user_id: Optional[str]


class UserActionBase(UserActionCreate):
    pass


class UserActionBaseState(BaseModel):
    state: bool


class UserAction(UserActionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserActionOut(UserAction):
    pass


class UserActionPatch(UserActionBase):
    pass
