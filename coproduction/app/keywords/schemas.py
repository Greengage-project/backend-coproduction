import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class KeywordBase(BaseModel):
    name: str
    description: Optional[str]


class KeywordCreate(KeywordBase):
    pass


class KeywordPatch(KeywordCreate):
    name: Optional[dict]


class Keyword(KeywordBase):
    id: uuid.UUID
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True


class KeywordOut(Keyword):
    pass