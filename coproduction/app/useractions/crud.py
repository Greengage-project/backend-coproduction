from app.messages import log
from typing import Any, Dict, Optional, List
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app.models import UserAction, User
from app.schemas import UserActionCreate, UserActionPatch
from app.sockets import socket_manager
from app import schemas, crud


class CRUDUserAction(
        CRUDBase[UserAction, UserActionCreate,
                 UserActionPatch]):
    async def get_multi(
            self, db: Session, user: User) -> Optional[List[UserAction]]:
        return db.query(UserAction).all()

    async def create(self, db: Session, obj_in: UserActionCreate
                     ) -> UserAction:
        user_id = obj_in.user_id
        user = None
        if not user_id:
            user = await crud.user.get(db, user_id)
            if not user:
                raise Exception("User not found")

        coproductionprocess_id = None
        if obj_in.coproductionprocess_id:
            coproductionprocess = await crud.coproductionprocess.get(db, obj_in.coproductionprocess_id)
            if not coproductionprocess:
                raise Exception("CoproductionProcess not found")
            coproductionprocess_id = coproductionprocess.id

        task_id = None
        if obj_in.task_id:
            task = await crud.task.get(db, obj_in.task_id)
            if not task:
                raise Exception("Task not found")
            task_id = task.id

        asset_id = None
        if obj_in.asset_id:
            asset = await crud.asset.get(db, obj_in.asset_id)
            if not asset:
                raise Exception("Asset not found")
            asset_id = asset.id

        obj_in_data = jsonable_encoder(obj_in)

        # Convertir el esquema Pydantic a una instancia del modelo SQLAlchemy
        db_obj = UserAction(**obj_in_data)
        print('_____________________________________________________')
        print('_____________________________________________________')
        print('_____________________________________________________')
        print('_____________________________________________________')
        print('_____________________________________________________')
        print('_____________________________________________________')
        print(db_obj)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        await socket_manager.broadcast({"event": "useraction_created"})

        await self.log_on_create(db_obj)
        return db_obj

    async def update(
        self,
        db: Session,
        db_obj: UserAction,
        obj_in: schemas.UserActionPatch
    ) -> UserAction:
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


exportCrud = CRUDUserAction(UserAction)
