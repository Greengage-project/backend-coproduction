import uuid
from sqlalchemy import (
    Enum,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Numeric,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import aggregated

from app.general.db.base_class import Base as BaseModel
from app.tasks.models import Status, Task
from sqlalchemy.ext.associationproxy import association_proxy

prerequisites = Table(
    'phase_prerequisites', BaseModel.metadata,
    Column('phase_a_id', ForeignKey('phase.id', ondelete="CASCADE"), primary_key=True),
    Column('phase_b_id', ForeignKey('phase.id', ondelete="CASCADE"), primary_key=True)
)

class Phase(BaseModel):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String)

    # prerequisites
    prerequisites = relationship("Phase", secondary=prerequisites,
                                 primaryjoin=id == prerequisites.c.phase_a_id,
                                 secondaryjoin=id == prerequisites.c.phase_b_id,
                                 )

    # they belong to a process
    coproductionprocess_id = Column(
        UUID(as_uuid=True), ForeignKey("coproductionprocess.id", ondelete='CASCADE')
    )
    coproductionprocess = relationship("CoproductionProcess", backref=backref('phases', passive_deletes=True))

    def __repr__(self):
        return "<Phase %r>" % self.name

    prerequisites_ids = association_proxy('prerequisites', 'id')

    @aggregated('objectives.tasks', Column(Date))
    def end_date(self):
        return func.max(Task.end_date)

    @aggregated('objectives.tasks', Column(Date))
    def start_date(self):
        return func.min(Task.start_date)

    status = Column(Enum(Status, create_constraint=False, native_enum=False), default=Status.awaiting)
    progress = Column(Numeric, default=0)
    