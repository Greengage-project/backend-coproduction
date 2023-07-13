import uuid
from typing import Optional, List

from pydantic import BaseModel
from app.general.utils.AllOptional import AllOptional
from datetime import datetime
from app.utils import ChannelTypes

class ParticipationRequestBase(BaseModel):
    candidate_id: str
    coproductionprocess_id: Optional[uuid.UUID]
    razon: Optional[str]
    is_archived: Optional[bool]
    
class ParticipationRequestArchive(BaseModel):
    is_archived: bool


class ParticipationRequest(ParticipationRequestBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ParticipationRequestOut(ParticipationRequest):
    pass

class ParticipationRequestPatch(ParticipationRequestBase):
    pass

class ParticipationRequestCreate(ParticipationRequestBase):
    pass