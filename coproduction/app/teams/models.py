import uuid

from sqlalchemy import Column, ForeignKey, String, Table, Integer, func, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship

from app.general.db.base_class import Base as BaseModel
from app.config import settings
from sqlalchemy.ext.associationproxy import association_proxy
from app.tables import user_team_association_table
from app.tables import team_administrators_association_table
from app.tables import team_applies_association_table
from sqlalchemy_utils import aggregated
from sqlalchemy.orm import Session
from app.utils import RoleTypes

# from app.tables import team_notification_association_table

class Team(BaseModel):
    """Team Class contains standard information for a Team."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=False, nullable=False)
    description = Column(String, nullable=False)
    logotype = Column(String, nullable=True)
    type = Column(Enum(RoleTypes, create_constraint=False, native_enum=False), nullable=False)

    # created by
    creator_id = Column(String, ForeignKey("user.id", use_alter=True, ondelete='SET NULL'))
    creator = relationship('User', foreign_keys=[creator_id], post_update=True, backref="created_teams")

    # belongs to
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organization.id', ondelete='CASCADE'))
    organization = relationship('Organization', foreign_keys=[organization_id], backref=backref('teams', passive_deletes=True))


    users = relationship(
        "User",
        secondary=user_team_association_table,
        backref="teams")
    user_ids = association_proxy('users', 'id')

    @aggregated('users', Column(Integer))
    def users_count(self):
        return func.count('1')

    administrators = relationship(
        "User",
        secondary=team_administrators_association_table,
        backref="administered_teams")
    administrators_ids = association_proxy('administrators', 'id')

    applies = relationship(
        "User",
        secondary=team_applies_association_table,
        backref="applied_teams")
    appliers_ids = association_proxy('applies', 'id')


    @property
    def logotype_link(self):
        return settings.COMPLETE_SERVER_NAME + self.logotype if self.logotype else ""

    @property
    def current_user_participation(self):
        from app.general.deps import get_current_user_from_context
        db = Session.object_session(self)
        participations = []
        if user := get_current_user_from_context(db=db):
            if user in self.administrators:
                participations.append("administrator")
            if user in self.users:
                participations.append("member")
        return participations