from email.policy import default
import uuid
from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Date,
    Text,
    Boolean,
    func
)
from sqlalchemy_utils import aggregated
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.general.db.base_class import Base as BaseModel
from app.config import settings
from app.phases.models import Phase
from sqlalchemy.ext.associationproxy import association_proxy
from app.tables import coproductionprocess_administrators_association_table, coproductionprocess_tags_association_table
from sqlalchemy.orm import Session
from app.utils import Status

class CoproductionProcess(BaseModel):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schema_used = Column(UUID(as_uuid=True))
    language = Column(String, default=settings.DEFAULT_LANGUAGE)
    name = Column(String)
    description = Column(String)

    logotype = Column(String, nullable=True)
    aim = Column(Text, nullable=True)
    idea = Column(Text, nullable=True)
    organization_desc = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)

    #Active Optional Modules
    incentive_and_rewards_state =Column(Boolean,nullable=True)

    #Optional field defined just by the user:
    #-------------
    hasAddAnOrganization =Column(Boolean,nullable=True)
    skipResourcesStep =Column(Boolean,nullable=True)
    hideguidechecklist =Column(Boolean,nullable=True)
    #-------------

    intergovernmental_model =Column(String,nullable=True)

    is_part_of_publication = Column(Boolean,nullable=True)
    is_public = Column(Boolean,nullable=True)

    status = Column(Enum(Status, create_constraint=False,
                    native_enum=False), default=Status.in_progress)
    
    # 1 digit for decimals
    rating= Column(Numeric(2, 1), default=0)
    ratings_count = Column(Integer, default=0) 


    # created by
    creator_id = Column(String, ForeignKey(
        "user.id", use_alter=True, ondelete='SET NULL'))
    creator = relationship('User', foreign_keys=[
                           creator_id], post_update=True, backref="created_coproductionprocesses")
    administrators = relationship(
        "User",
        secondary=coproductionprocess_administrators_association_table,
        backref="administered_processes")
    administrators_ids = association_proxy('administrators', 'id')

    organization_id = Column(UUID(as_uuid=True), ForeignKey(
        "organization.id", use_alter=True, ondelete='SET NULL'))
    organization = relationship('Organization', post_update=True, backref="coproductionprocesses")

    teams = association_proxy('permissions', 'team')


    coproductionprocess_notification_associations = relationship(
        "CoproductionProcessNotification",
        back_populates="coproductionprocess",
        cascade="all, delete-orphan",
    )
    notifications = association_proxy("coproductionprocess_notification_associations", "notification")

    coproductionprocess_story_associations = relationship(
        "Story",
        back_populates="coproductionprocess",
        cascade="all, delete-orphan",
    )
    
    # Gamification
    game_id = Column(String, nullable=True)
    
    # Tags
    tags = relationship(
        'Tag',
        secondary=coproductionprocess_tags_association_table,
        backref='coproductionprocesses',
    )
    tags_ids = association_proxy('tags', 'id')
    
    
    stories = association_proxy("coproductionprocess_story_associations", "story")
    
    cloned_from_id = Column(UUID(as_uuid=True), ForeignKey('coproductionprocess.id', ondelete='CASCADE', name='fk_copro_id_cloned_from'), nullable=True)
    cloned_to = relationship("CoproductionProcess", backref=backref("cloned_from", remote_side=[id]))
    
    @aggregated('children', Column(Date))
    def end_date(self):
        return func.max(Phase.end_date)

    @aggregated('children', Column(Date))
    def start_date(self):
        return func.min(Phase.start_date)

    # the tree items can be disabled, so we need to retrieve only those teams or permissions that are not disabled
    @property
    def enabled_teams(self):
        return [perm.team for perm in self.permissions if not perm.treeitem or (perm.treeitem and not perm.treeitem.disabled_on)]
    
    @property
    def enabled_permissions(self):
        return [perm for perm in self.permissions if not perm.treeitem or (perm.treeitem and not perm.treeitem.disabled_on)]

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
            else:
                participations.append("collaborator")
        return participations

    def task_ids(self):
        res = []
        for phase in self.children:
            if not phase.disabled_on:
                for objective in phase.children:
                    if not objective.disabled_on:
                        for task in objective.children:
                            if not task.disabled_on:
                                res.append(task.id)
        return res
    


    # Define the serialize function
    def to_dict(self):
        return {
            'id': str(self.id),
            'schema_used': str(self.schema_used),
            'language': self.language,
            'name': self.name,
            'description': self.description,
            'logotype': self.logotype,
            'aim': self.aim,
            'idea': self.idea,
            'organization_desc': self.organization_desc,
            'challenges': self.challenges,
            'requirements': self.requirements,
            'incentive_and_rewards_state': self.incentive_and_rewards_state,
            'hasAddAnOrganization': self.hasAddAnOrganization,
            'skipResourcesStep': self.skipResourcesStep,
            'hideguidechecklist': self.hideguidechecklist,
            'intergovernmental_model': self.intergovernmental_model,
            'is_part_of_publication': self.is_part_of_publication,
            'is_public': self.is_public,
            'status': self.status,
            'rating': str(self.rating),
            'ratings_count': self.ratings_count,
            'administrators': [admin.email for admin in self.administrators],
            'tags': [str(tag.name) for tag in self.tags],
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'logotype_link': self.logotype_link,

        }

