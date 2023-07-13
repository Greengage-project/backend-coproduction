import uuid
from typing import Optional, List

from pydantic import BaseModel
from app.general.utils.AllOptional import AllOptional
from datetime import datetime
from app.utils import ChannelTypes

class AssignmentBase(BaseModel):
    user_id: str
    asset_id: Optional[uuid.UUID]
    task_id: Optional[uuid.UUID]
    coproductionprocess_id: Optional[uuid.UUID]
    title: Optional[str]
    description: Optional[str]
    state: Optional[bool]
    
class AssignmentApproved(BaseModel):
    state: bool


class Assignment(AssignmentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class AssignmentOut(Assignment):
    pass

class AssignmentPatch(AssignmentBase):
    pass

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentCreateUserList(BaseModel):
    users_id: List[str]
    asset_id: Optional[uuid.UUID]
    task_id: Optional[uuid.UUID]
    coproductionprocess_id: Optional[uuid.UUID]
    title: Optional[str]
    description: Optional[str]
    state: Optional[bool]
    pass

class AssignmentCreateTeamList(BaseModel):
    teams_id: List[str]
    asset_id: Optional[uuid.UUID]
    task_id: Optional[uuid.UUID]
    coproductionprocess_id: Optional[uuid.UUID]
    title: Optional[str]
    description: Optional[str]
    state: Optional[bool]
    pass