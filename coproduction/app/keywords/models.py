from sqlalchemy import (
    Column
)
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String
from app.general.db.base_class import Base as BaseModel

from sqlalchemy.ext.associationproxy import association_proxy


class Keyword(BaseModel):
    """
    Defines the keyword model
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    stories_ids = association_proxy('stories', 'id')


    def __repr__(self) -> str:
        return f"<Keyword {self.name}>"
