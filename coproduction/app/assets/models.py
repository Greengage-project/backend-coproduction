import json
import uuid
from typing import TypedDict
import requests
from sqlalchemy import (
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
from sqlalchemy import orm
from sqlalchemy.ext.associationproxy import association_proxy

from app.config import settings
from app.general.db.base_class import Base as BaseModel
from cached_property import cached_property


class Asset(BaseModel):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # discriminator
    type = Column(String)

    task_id = Column(UUID(as_uuid=True), ForeignKey(
        "task.id", ondelete='CASCADE'))
    task = orm.relationship("Task", backref=orm.backref(
        'assets', passive_deletes=True))

    # to simplify queries
    objective_id = Column(UUID(as_uuid=True))
    phase_id = Column(UUID(as_uuid=True))
    coproductionprocess_id = Column(UUID(as_uuid=True))

    # created by
    creator_id = Column(String, ForeignKey(
        "user.id", use_alter=True, ondelete='SET NULL'))
    creator = orm.relationship('User', foreign_keys=[
                               creator_id], post_update=True, backref="created_assets")

    # asset_copronotification_associations = orm.relationship(
    #     "CoproductionProcessNotification",
    #     back_populates="asset"
    # )
    # copronotifications = association_proxy("asset_copronotification_associations", "copronotification")

    __mapper_args__ = {
        "polymorphic_identity": "asset",
        "polymorphic_on": type,
    }

    def __repr__(self):
        return f"<Asset(id={self.id}, type='{self.type}', task_id={self.task_id}, creator_id={self.creator_id})>"

    def __str__(self):
        return f"Asset (ID: {self.id}, Type: {self.type}, Task ID: {self.task_id})"

    def to_dict(self):
        """
        Convierte la instancia en un diccionario, útil para serialización.
        """
        return {
            "id": str(self.id),
            "type": self.type,
            "task_id": str(self.task_id) if self.task_id else None,
            "objective_id": str(self.objective_id) if self.objective_id else None,
            "phase_id": str(self.phase_id) if self.phase_id else None,
            "coproductionprocess_id": str(self.coproductionprocess_id) if self.coproductionprocess_id else None,
            "creator_id": self.creator_id
        }


class InternalAsset(Asset):
    id = Column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete='CASCADE'),
        primary_key=True,
        default=uuid.uuid4,
    )
    external_asset_id = Column(String)
    softwareinterlinker_id = Column(UUID(as_uuid=True))
    # save from which knowledge interlinker has been cloned, if so
    knowledgeinterlinker_id = Column(UUID(as_uuid=True), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "internalasset",
    }

    def __repr__(self):
        return "<Asset %r>" % self.id

    @cached_property
    def software_response(self):
        return requests.get(
            f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{self.softwareinterlinker_id}").json()

    @cached_property
    def knowledge_response(self):
        if self.knowledgeinterlinker_id:
            return requests.get(
                f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{self.knowledgeinterlinker_id}").json()
        return

    @property
    def knowledgeinterlinker(self):
        return {
            "id": self.knowledge_response.get("id"),
            "name": self.knowledge_response.get("name"),
            "description": self.knowledge_response.get("description"),
            "logotype_link": self.knowledge_response.get("logotype_link"),
        } if self.knowledge_response else None

    @property
    def link(self):
        backend = self.software_response.get("backend")
        return f"{backend}/{self.external_asset_id}"

    @property
    def internal_link(self):
        backend = self.software_response.get("service_name")
        api_path = self.software_response.get("api_path")
        return f"http://{backend}{api_path}/{self.external_asset_id}"

    @property
    def softwareinterlinker(self):
        return {
            "id": self.software_response.get("id"),
            "name": self.software_response.get("name"),
            "description": self.software_response.get("description"),
            "logotype_link": self.software_response.get("logotype_link"),
        } if self.software_response else None

    @property
    def capabilities(self):
        return {
            "clone": self.software_response.get("clone"),
            "view": self.software_response.get("view"),
            "edit": self.software_response.get("edit"),
            "delete": self.software_response.get("delete"),
            "download": self.software_response.get("download"),
        }


class ExternalAsset(Asset):
    id = Column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete='CASCADE'),
        primary_key=True,
        default=uuid.uuid4,
    )
    name = Column(String)
    icon_path = Column(String)
    externalinterlinker_id = Column(UUID(as_uuid=True))
    uri = Column(String)

    @property
    def icon(self):
        return settings.COMPLETE_SERVER_NAME + self.icon_path if self.icon_path else ""

    __mapper_args__ = {
        "polymorphic_identity": "externalasset",
    }

    @cached_property
    def external_response(self):
        if self.externalinterlinker_id:
            return requests.get(f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{self.externalinterlinker_id}").json()
        return

    @property
    def externalinterlinker(self):
        return {
            "id": self.external_response.get("id"),
            "name": self.external_response.get("name"),
            "description": self.external_response.get("description"),
            "logotype_link": self.external_response.get("logotype_link"),
        } if self.external_response else None
