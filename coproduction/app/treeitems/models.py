import copy
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Table, or_, and_, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Session, relationship

from app.general.db.base_class import Base as BaseModel
from app.permissions.models import Permission
from app.teams.models import Team
from app.utils import cached_hybrid_property, Status

prerequisites = Table(
    'treeitem_prerequisites', BaseModel.metadata,
    Column('treeitem_a_id', ForeignKey(
        'treeitem.id', ondelete="CASCADE"), primary_key=True),
    Column('treeitem_b_id', ForeignKey(
        'treeitem.id', ondelete="CASCADE"), primary_key=True)
)



class TreeItem(BaseModel):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(70))
    name = Column(String)
    description = Column(String)

    # prerequisites
    prerequisites = relationship("TreeItem", secondary=prerequisites,
                                 primaryjoin=id == prerequisites.c.treeitem_a_id,
                                 secondaryjoin=id == prerequisites.c.treeitem_b_id,
                                 )

    prerequisites_ids = association_proxy('prerequisites', 'id')

    # created by
    creator_id = Column(String, ForeignKey(
        "user.id", use_alter=True, ondelete='SET NULL'))
    creator = relationship('User', foreign_keys=[
                           creator_id], post_update=True, backref="created_treeitems")

    # state
    status = Column(Enum(Status, create_constraint=False,
                    native_enum=False), default=Status.awaiting)

    # Disabled by
    disabler_id = Column(String, ForeignKey(
        "user.id", use_alter=True, ondelete='SET NULL'))
    disabler = relationship('User', foreign_keys=[
                            disabler_id], post_update=True, backref="disabled_treeitems")
    disabled_on = Column(DateTime)

    from_item = Column(UUID(as_uuid=True))
    from_schema = Column(UUID(as_uuid=True))

    # teams = association_proxy('_permissions', 'team')

    __mapper_args__ = {
        "polymorphic_identity": "treeitem",
        "polymorphic_on": type,
    }

    @cached_hybrid_property
    def permissions(self):
        db = Session.object_session(self)
        # Get permissions of the treeitem teams of the user
        return db.query(
            Permission
        ).filter(
            or_(
                and_(
                    Permission.coproductionprocess_id == self.coproductionprocess.id,
                    Permission.treeitem_id == None
                ),
                and_(
                    Permission.treeitem_id.in_(self.path_ids),
                    Permission.coproductionprocess_id == self.coproductionprocess.id
                ),
            )
        ).all()
    
    @cached_hybrid_property
    def teams(self):
        t = []
        ids = []
        for permission in self.permissions:
            if permission.team_id not in ids:
                t.append(permission.team)
                ids.append(permission.team_id)
        return t

    @cached_hybrid_property
    def user_roles(self):
        from app.general.deps import get_current_user_from_context
        from app.permissions.crud import exportCrud

        db = Session.object_session(self)
        if user := get_current_user_from_context(db=db):
            return exportCrud.get_user_roles(db=db, user=user, treeitem=self)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'type': self.type,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,  # Assuming `Status` is an Enum
            'creator_id': self.creator_id,
            'disabler_id': self.disabler_id,
            'disabled_on': self.disabled_on.isoformat() if self.disabled_on else None,
            'from_item': str(self.from_item) if self.from_item else None,
            'from_schema': str(self.from_schema) if self.from_schema else None,
            'prerequisites_ids': [str(prereq.id) for prereq in self.prerequisites]
        }