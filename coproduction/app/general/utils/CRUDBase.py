import logging
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from uuid_by_string import generate_uuid

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session, make_transient
from sqlalchemy import or_, and_
from fastapi import HTTPException

from app.general.db.base_class import Base
from app.messages import log
from app.users.models import User
from app.config import settings
from app.sockets import socket_manager

from app.general.emails import send_email

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
PatchSchemaType = TypeVar("PatchSchemaType", bound=BaseModel)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CRUDBase(Generic[ModelType, CreateSchemaType, PatchSchemaType]):
    def __init__(self, model: Type[ModelType], logByDefault=False):
        """
        CRUD object with default methods to Create, Read, Patch, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.logByDefault = logByDefault
        self.modelName = model.__name__.upper()
        self.model = model

    async def get(self, db: Session, id: uuid.UUID) -> Optional[ModelType]:
        if obj := db.query(self.model).filter(self.model.id == id).first():
            await self.log_on_get(obj)
            return obj
        return

    async def get_multi_by_ids(self, db: Session, ids: list) -> List[ModelType]:
        return db.query(self.model).filter(self.model.id.in_(ids)).all()

    async def get_by_name(self, db: Session, name: str) -> Optional[ModelType]:
        if obj := db.query(self.model).filter(self.model.name == name).first():
            await self.log_on_get(obj)
            return obj
        return
    
    async def get_multi_by_name(self, db: Session, name: str) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.name == name).all()

    async def get_by_name_translation(self, db: Session, name: str, language: str = settings.DEFAULT_LANGUAGE) -> Optional[ModelType]:
        if obj := db.query(self.model).filter(self.model.name_translations[language] == name).first():
            await self.log_on_get(obj)
            return obj
        return

    async def get_by_name_translations(self, db: Session, name_translations: str) -> Optional[ModelType]:
        return db.query(self.model).filter(
            or_(
                and_(self.model.name_translations["en"] != None,
                     self.model.name_translations["en"] == name_translations["en"]),
                and_(self.model.name_translations["es"] != None,
                     self.model.name_translations["es"] == name_translations["es"]),
                and_(self.model.name_translations["it"] != None,
                     self.model.name_translations["it"] == name_translations["it"]),
                and_(self.model.name_translations["lv"] != None,
                     self.model.name_translations["lv"] == name_translations["lv"]),
            ),
        ).first()
    
    async def get_by_name_translations_value(self, db: Session, name_translations: str) -> Optional[ModelType]:
        return db.query(self.model).filter(
            or_(
                and_(self.model.name_translations["en"] != None,
                     self.model.name_translations["en"] == name_translations),
                and_(self.model.name_translations["es"] != None,
                     self.model.name_translations["es"] == name_translations),
                and_(self.model.name_translations["it"] != None,
                     self.model.name_translations["it"] == name_translations),
                and_(self.model.name_translations["lv"] != None,
                     self.model.name_translations["lv"] == name_translations),
            ),
        ).first()

    async def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).order_by(self.model.created_at.asc()).offset(skip).limit(limit).all()

    async def create(self, db: Session, *, obj_in: CreateSchemaType, creator: User = None, set_creator_admin: bool = False, extra: dict = {}, commit: bool = True) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, **extra)  # type: ignore

        if creator:
            db_obj.creator_id = creator.id
            if set_creator_admin:
                db_obj.administrators.append(creator)

        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
            await self.log_on_create(db_obj)

        if self.modelName == "COPRODUCTIONPROCESS":
            await socket_manager.send_to_id(db_obj.id, {"event": self.modelName.lower() + "_created"})
        elif hasattr(db_obj, "coproductionprocess_id"):

            await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": self.modelName.lower() + "_created"})

        # Send info to private socket to update workspace page
        if hasattr(db_obj, "team") and self.modelName == "PERMISSION":
            for user in db_obj.team.users:
                await socket_manager.send_to_id(generate_uuid(user.id), {"event": self.modelName.lower() + "_created"})
        # Send info when you create an organization
        if self.modelName == "ORGANIZATION":
            await socket_manager.broadcast({"event": self.modelName.lower() + "_created"})

        return db_obj

    async def add_administrator(self, db: Session, *, db_obj: ModelType, user: User = None, notifyAfterAdded: bool = True) -> ModelType:
        from app.worker import sync_asset_users
        db_obj.administrators.append(user)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Sincroniza los usuarios administradores con cada uno de los assets:
        if notifyAfterAdded:
            sync_asset_users([user.id])
            enriched: dict = self.enrich_log_data(db_obj, {
                "action": "ADD_ADMINISTRATOR",
                "added_user_id": user.id
            })
            await log(enriched)

            if self.modelName == "COPRODUCTIONPROCESS":
                await socket_manager.send_to_id(db_obj.id, {"event": self.modelName.lower() + "_administrator_added"})
            if hasattr(db_obj, "coproductionprocess_id"):
                await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": self.modelName.lower() + "_administrator_added"})

            # Send info to private socket to update workspace page
            await socket_manager.send_to_id(generate_uuid(user.id), {"event": self.modelName.lower() + "_administrator_added"})

            # Send mail to user to know is added to a team
            _ = send_email(user.email,
                           'add_admin_coprod',
                           {"coprod_id": db_obj.id,
                            "coprod_name": db_obj.name, })

        return db_obj

    async def remove_administrator(self, db: Session, *, db_obj: ModelType, user: User = None) -> ModelType:
        from app.worker import sync_asset_users
        if len(db_obj.administrators) <= 1:
            raise HTTPException(
                status_code=400, detail="Can not delete the last administrator")

        db_obj.administrators.remove(user)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        sync_asset_users([user.id])
        enriched: dict = self.enrich_log_data(db_obj, {
            "action": "REMOVE_ADMINISTRATOR",
            "removed_user_id": user.id
        })
        await log(enriched)

        if self.modelName == "COPRODUCTIONPROCESS":
            await socket_manager.send_to_id(db_obj.id, {"event": self.modelName.lower() + "_administrator_removed"})
        elif hasattr(db_obj, "coproductionprocess_id"):
            await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": self.modelName.lower() + "_administrator_removed"})

        # Send info to private socket to update workspace page
        await socket_manager.send_to_id(generate_uuid(user.id), {"event": self.modelName.lower() + "_administrator_removed"})

        return db_obj

    async def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[PatchSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        #print("update_data", update_data)
        for field, value in update_data.items():
            if hasattr(db_obj, field) and value != getattr(db_obj, field):
                #print("Updating", field)
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        await self.log_on_update(db_obj)

        if self.modelName == "COPRODUCTIONPROCESS":
            await socket_manager.send_to_id(db_obj.id, {"event": self.modelName.lower() + "_updated"})
        elif hasattr(db_obj, "coproductionprocess_id"):
            await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": self.modelName.lower() + "_updated"})

        # Send info when you create an team
        if self.modelName == "TEAM":
            await socket_manager.broadcast({"event": self.modelName.lower() + "_updated"})

        # Send info when you create an team
        if self.modelName == "ORGANIZATION":
            await socket_manager.broadcast({"event": self.modelName.lower() + "_updated"})

        return db_obj

    async def remove(self, db: Session, *, id: uuid.UUID) -> ModelType:
        db_obj = db.query(self.model).get(id)
        await self.log_on_remove(db_obj)

        db.delete(db_obj)
        db.commit()

        # General case where a (coproductionprocess_removed)
        if self.modelName == "COPRODUCTIONPROCESS":
            await socket_manager.send_to_id(db_obj.id, {"event": self.modelName.lower() + "_removed"})

        elif hasattr(db_obj, "coproductionprocess_id"):

            # The case of the asset is (asset_removed)
            if self.modelName == "ASSET":
                await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": self.modelName.lower() + "_removed", "extra": {"task_id": jsonable_encoder(db_obj.task_id)}})
            else:
                # Any other case:
                await socket_manager.send_to_id(db_obj.coproductionprocess_id, {"event": self.modelName.lower() + "_removed"})

        # # Send info to private socket to update workspace page
        if hasattr(db_obj, "team") and self.modelName == "PERMISSION":
            for user in db_obj.team.users:
                await socket_manager.send_to_id(generate_uuid(user.id), {"event": self.modelName.lower() + "_removed"})

        # Send info when you create an organization
        if self.modelName == "ORGANIZATION":
            await socket_manager.broadcast({"event": self.modelName.lower() + "_removed"})

        # Send info when you create an team
        if self.modelName == "TEAM":
            await socket_manager.broadcast({"event": self.modelName.lower() + "_removed"})

        return None

    # LOGS

    async def log_on_get(self, obj):
        # enriched : dict  = self.enrich_log_data(obj, {
        #     "action": "GET"
        # })
        # await log(enriched)
        pass

    async def log_on_create(self, obj):
        enriched: dict = self.enrich_log_data(obj, {
            "action": "CREATE"
        })
        await log(enriched)

    async def log_on_update(self, obj):
        enriched: dict = self.enrich_log_data(obj, {
            "action": "UPDATE"
        })
        await log(enriched)

    async def log_on_remove(self, obj):
        enriched: dict = self.enrich_log_data(obj, {
            "action": "DELETE"
        })
        await log(enriched)

    def enrich_log_data(self, obj, logData) -> dict:
        logData["model"] = self.modelName
        logData["object_id"] = obj.id
        return logData

    # CRUD Permissions

    def can_create(self, user):
        logger.warn("You need to override can_create of the crud")
        return True

    def can_list(self, user):
        logger.warn("You need to override can_list of the crud")
        return True

    def can_read(self, user, object):
        logger.warn("You need to override can_read of the crud")
        return True

    def can_update(self, user, object):
        logger.warn("You need to override can_update of the crud")
        return True

    def can_remove(self, user, object):
        logger.warn("You need to override can_remove of the crud")
        return True
