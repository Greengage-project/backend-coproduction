import uuid
from typing import Optional, List

from pydantic import BaseModel
from app.general.utils.AllOptional import AllOptional
from datetime import datetime
from app.utils import ChannelTypes

class ClaimBase(BaseModel):
    user_id: str
    asset_id: Optional[uuid.UUID]
    task_id: Optional[uuid.UUID]
    coproductionprocess_id: Optional[uuid.UUID]
    assignment_id: Optional[uuid.UUID]
    title: Optional[str]
    description: Optional[str]
    state: Optional[bool]
    claim_type: Optional[str]
    
class ClaimApproved(BaseModel):
    state: bool


class Claim(ClaimBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ClaimOut(Claim):
    pass

class ClaimPatch(ClaimBase):
    pass

class ClaimCreate(ClaimBase):
    pass

class ClaimCreateUserList(BaseModel):
    users_id: List[str]
    asset_id: Optional[uuid.UUID]
    task_id: Optional[uuid.UUID]
    coproductionprocess_id: Optional[uuid.UUID]
    title: Optional[str]
    description: Optional[str]
    state: Optional[bool]
    claim_type: Optional[str]
    pass

class ClaimCreateTeamList(BaseModel):
    teams_id: List[str]
    asset_id: Optional[uuid.UUID]
    task_id: Optional[uuid.UUID]
    coproductionprocess_id: Optional[uuid.UUID]
    title: Optional[str]
    description: Optional[str]
    state: Optional[bool]
    claim_type: Optional[str]
    pass