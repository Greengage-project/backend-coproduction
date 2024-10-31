from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app import models
from app.schemas import UserCreate, UserPatch
import uuid
from sqlalchemy import and_, func, or_
from app.treeitems.crud import exportCrud as treeitemsCrud


class CRUDUser(CRUDBase[models.User, UserCreate, UserPatch]):
    async def search(
        self,
        db: Session,
        user: models.User,
        search: str,
        organization_id: uuid.UUID = None,
    ) -> List[models.User]:
        if organization_id:
            print("Searching in org")
            se = search.lower()

            teams = (
                db.query(models.Team)
                .filter(models.Team.organization_id == organization_id)
                .all()
            )
            return (
                db.query(models.User)
                .filter(
                    or_(
                        and_(
                            models.User.teams.any(
                                models.Team.id.in_([team.id for team in teams])
                            ),
                            or_(
                                models.User.full_name.ilike(f"%{se}%"),
                                models.User.email.ilike(f"%{se}%"),
                            ),
                        ),
                        models.User.email == search,
                    )
                )
                .all()
            )
        else:
            print("Searching by email")
            # only retrieve if the email is exact
            if res := db.query(models.User).filter(models.User.email == search).first():
                return [res]
            return []

    async def get(self, db: Session, id: uuid.UUID) -> Optional[models.User]:
        if (
            obj := db.query(models.User)
            .filter(or_(models.User.id == id, models.User.email == id))
            .first()
        ):
            await self.log_on_get(obj)
            return obj
        return

    async def get_users(self, db: Session, ids: List[uuid.UUID]) -> List[models.User]:
        # retrieve only  "picture" , "full_name" and "id" fields
        # return db.query(models.User).filter(models.User.id.in_(ids)).all()
        db_obj = db.query(models.User).filter(models.User.id.in_(ids)).all()
        response = []
        for user in db_obj:
            response.append(
                {
                    "id": user.id,
                    "full_name": user.full_name,
                    "picture": user.picture,
                }
            )

        return response

    async def getUser(self, db: Session, id: str) -> Optional[models.User]:
        if (
            obj := db.query(models.User)
            .filter(
                models.User.id == id,
            )
            .first()
        ):
            return obj
        return

    async def update_or_create(self, db: Session, data: dict) -> Optional[models.User]:
        from app.worker import sync_asset_users

        if "sub" in data:
            data["id"] = data.get("sub")
            if user := await self.get(db=db, id=data.get("id")):
                if data.get("additionalEmails", []) != user.additionalEmails:
                    sync_asset_users.delay(user_ids=[user.id])

                return await self.update(db=db, db_obj=user, obj_in=UserPatch(**data))
            else:
                return await self.create(db=db, obj_in=UserCreate(**data))
        raise Exception("Sub not in data")

    # Override log methods
    def enrich_log_data(self, obj, logData):
        logData["model"] = "USER"
        logData["object_id"] = obj.id
        return logData

    async def log_on_update(self, obj):
        # user updated frequently => do not log
        return

    # CRUD Permissions
    def can_create(self, user):
        return True

    def can_list(self, user):
        return True

    def can_read(self, user, object):
        return True

    def can_update(self, user, object):
        return True

    def can_remove(self, user, object):
        return True


exportCrud = CRUDUser(models.User, logByDefault=True)
