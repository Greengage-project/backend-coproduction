import uuid

from app.general.db.base_class import Base as BaseModel
from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref


class Rating(BaseModel):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)
    artefact_id = Column(UUID(as_uuid=True))
    artefact_type = Column(String)
    title = Column(String, nullable=True)
    text = Column(Text)
    value = Column(Integer)
