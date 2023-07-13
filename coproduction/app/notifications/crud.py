from app.messages import log
from typing import Any, Dict, Optional, List

from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app.models import Notification, UserNotification, User, Organization
from app.schemas import NotificationCreate, NotificationPatch, UserNotificationCreate, UserNotificationPatch
import uuid
from app import models
from app.users.crud import exportCrud as users_crud

from sqlalchemy import or_, and_
from fastapi.encoders import jsonable_encoder
from app.sockets import socket_manager
from uuid_by_string import generate_uuid
from app import schemas


class CRUDNotification(CRUDBase[Notification, NotificationCreate, NotificationPatch]):
    async def get_multi(self, db: Session, user: User) -> Optional[List[Notification]]:
        return db.query(Notification).all()

    # Get all notifications by Event:

    async def get_notification_by_event(self, db: Session, event: str, language: str) -> Optional[List[UserNotification]]:
        # print("Entra en notification  by event")
        # print(event)
        # print(language)
        notification = db.query(Notification).filter(and_(
            models.Notification.event == event,
            models.Notification.language == language
        )).first()
        # print(notification)
        return notification

    async def get_notification_by_id(self, db: Session, id:  uuid.UUID) -> Optional[List[UserNotification]]:
        notification = db.query(Notification).filter(
            models.Notification.id == id).first()
        return notification

    async def create(self, db: Session, obj_in: NotificationCreate) -> Notification:
        obj_in_data = jsonable_encoder(obj_in)

        db_obj = Notification(**obj_in_data)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        await socket_manager.broadcast({"event": "notification_created"})

        await self.log_on_create(db_obj)
        return db_obj

    async def update(
        self,
        db: Session,
        db_obj: Notification,
        obj_in: schemas.NotificationPatch
    ) -> Notification:
        obj_data = jsonable_encoder(db_obj)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        await self.log_on_update(db_obj)
        return db_obj


exportCrud = CRUDNotification(Notification)
