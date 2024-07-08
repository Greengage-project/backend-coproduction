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
from app.coproductionprocesses.models import CoproductionProcess
from app.tasks.models import Task
from app.assets.models import Asset


class UserAction(BaseModel):
    """Association Class contains for User's actions."""
    __tablename__ = "useraction"
    # user_id can be null if the user is not logged in
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        String, ForeignKey("user.id", ondelete='CASCADE'),
        nullable=True)

    coproductionprocess_id = Column(
        UUID(as_uuid=True),
        ForeignKey("coproductionprocess.id",
                   use_alter=True, ondelete='SET NULL'), nullable=True)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("task.id",
                                       use_alter=True, ondelete='SET NULL'),

        nullable=True)
    asset_id = Column(UUID(as_uuid=True),
                      ForeignKey("asset.id", use_alter=True,
                                 ondelete='SET NULL'),

                      nullable=True)
    path = Column(String, nullable=False)
    data = Column(JSON, nullable=True)
    section = Column(String, nullable=True)
    action = Column(String, nullable=False)

    user = relationship("User", foreign_keys=[
        user_id], backref=backref('user_actions',
                                  passive_deletes=True))
