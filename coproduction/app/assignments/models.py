import uuid

from sqlalchemy import Column, ForeignKey, String, Table, Integer, func, Boolean, Enum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship, declarative_base
from sqlalchemy.orm import Mapped
from typing import List

from app.general.db.base_class import Base as BaseModel
from app.config import settings
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_utils import aggregated
from sqlalchemy.orm import Session
from app.utils import ChannelTypes
from app.users.models import User

class Assignment(BaseModel):
    """Association Class contains for a Notification and User."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        String, ForeignKey("user.id", ondelete='CASCADE')
    )
    user = relationship("User", foreign_keys=[user_id], backref=backref('assignments', passive_deletes=True))

    asset_id = Column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete='CASCADE')
    )
    asset = relationship("Asset", foreign_keys=[asset_id], backref=backref('assignments', passive_deletes=True))
    
    task_id = Column(UUID(as_uuid=True), nullable=True)
    coproductionprocess_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    state = Column(Boolean, nullable=True, default=False)

     # add the relationship to claims
    claims = relationship('Claim', backref='assignment')

    def __repr__(self) -> str:
        return f"<Assignment {self.id} {self.user.name} {self.title} {self.state}>"