import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TagBase(BaseModel):
    name: str
    description: Optional[str]


class TagCreate(TagBase):
    pass


class TagPatch(TagCreate):
    name: Optional[dict]


class Tag(TagBase):
    id: uuid.UUID
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True


class TagOut(Tag):
    pass