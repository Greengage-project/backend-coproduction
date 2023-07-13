import uuid
from typing import Optional, List

from pydantic import BaseModel
from app.general.utils.AllOptional import AllOptional
from datetime import date, datetime
from app.utils import ChannelTypes
from app.utils import ClaimTypes
from typing import Dict,Any


class StoryBase(BaseModel):
    coproductionprocess_id: uuid.UUID
    coproductionprocess_cloneforpub_id: uuid.UUID
    data_story: Optional[dict]
    user_id: Optional[str]
    state: bool
    published_date: Optional[date]
    rating: Optional[float]
    ratings_count: Optional[int]
    logotype: Optional[str]
    keywords: Optional[List]
 

class Story(StoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True



class StoryOut(Story):
    pass

class StoryPatch(StoryBase):
    pass

class StoryCreate(StoryBase):
    pass