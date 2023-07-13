from sqlalchemy import (
    Column
)
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String
from app.general.db.base_class import Base as BaseModel

from sqlalchemy.ext.associationproxy import association_proxy


class Tag(BaseModel):
    """
    Defines the tag model
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    coproductionprocesses_ids = association_proxy('coproductionprocesses', 'id')


    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
