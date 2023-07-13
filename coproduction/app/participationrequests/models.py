import uuid

from sqlalchemy import Column, ForeignKey, String, Table, Integer, func, Boolean, Enum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship, declarative_base

from app.general.db.base_class import Base as BaseModel
from app.config import settings
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_utils import aggregated
from sqlalchemy.orm import Session
from app.utils import ChannelTypes
from app.users.models import User

class ParticipationRequest(BaseModel):
    """Association Class contains for a Notification and User."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        String, ForeignKey("user.id", ondelete='CASCADE')
    )
    
    user = relationship("User", foreign_keys=[
                             candidate_id], backref=backref('participation_requests', passive_deletes=True))
    coproductionprocess_id = Column(UUID(as_uuid=True), nullable=True)
    razon = Column(String, nullable=True)
    is_archived = Column(Boolean, nullable=True, default=False)


    
    def __repr__(self) -> str:
        return f"<ParticipationRequest {self.id} {self.user.name} {self.razon} {self.is_archived}>"