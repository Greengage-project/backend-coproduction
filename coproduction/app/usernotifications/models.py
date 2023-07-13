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

class UserNotification(BaseModel):
    """Association Class contains for a Notification and User."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("user.id", use_alter=True, ondelete='SET NULL'), nullable=False)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notification.id", use_alter=True, ondelete='SET NULL'), nullable=False)
    channel = Column(Enum(ChannelTypes, create_constraint=False, native_enum=False), nullable=False)
    state = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=True, default=False)

    coproductionprocess_id = Column(UUID(as_uuid=True), nullable=True)

    #Json object with information relevant to a notification:
    parameters = Column(JSON, nullable=True)
    
    notification = relationship('Notification', post_update=True, back_populates="users")
    user = relationship('User', back_populates="user_notification_associations")
    
    def __repr__(self) -> str:
        return f"<UserNotification {self.id} {self.channel} {self.state} {self.notification_id}>"