import uuid
from typing import Optional, List

from pydantic import BaseModel
from app.general.utils.AllOptional import AllOptional
from datetime import datetime
from app.utils import ChannelTypes

class UserNotificationBase(BaseModel):
    user_id: str
    notification_id: uuid.UUID
    channel: ChannelTypes
    state: bool
    is_archived: Optional[bool]
    coproductionprocess_id: Optional[uuid.UUID]
    parameters: Optional[str]

class UserNotificationState(BaseModel):
    state: bool

class UserNotificationArchive(BaseModel):
    is_archived: bool


class UserNotification(UserNotificationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserNotificationOut(UserNotification):
    pass

class UserNotificationPatch(UserNotificationBase):
    pass

class UserNotificationCreate(UserNotificationBase):
    pass