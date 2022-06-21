from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app import models
from app.schemas import UserCreate, UserPatch
import uuid
from sqlalchemy import and_, func, or_

class CRUDUser(CRUDBase[models.User, UserCreate, UserPatch]):
    async def search(self, db: Session, user: models.User, search: str, organization_id: uuid.UUID = None) -> List[models.User]:
        if organization_id:
            print("Searching in org")
            se = search.lower()

            teams = db.query(models.Team).filter(
                        or_(
                            models.Team.administrators.any(models.User.id.in_([user.id])),
                            models.Team.users.any(models.User.id.in_([user.id])),
                            models.Team.public == True,
                        ),
                        models.Team.organization_id == organization_id
            ).all()
            return db.query(
                    models.User
                ).filter(
                    or_(
                        and_(
                            models.User.teams.any(models.Team.id.in_([team.id for team in teams])),
                            or_(
                                models.User.full_name.ilike(f"%{se}%"),                
                                models.User.email.ilike(f"%{se}%"),                
                            )  
                        ),
                        models.User.email == search      
                    )
                ).all()
        else:
            print("Searching by email")
            # only retrieve if the email is exact
            return [
                db.query(models.User).filter(
                    models.User.email == search
                ).first()
            ]

    async def get(self, db: Session, id: uuid.UUID) -> Optional[models.User]:
        if obj := db.query(models.User).filter(
            or_(
                models.User.id == id,
                models.User.email == id
            )
        ).first():
            await self.log_on_get(obj)
            return obj
        return

    async def get_or_create(self, db: Session, data: dict) -> Optional[models.User]:
        if "sub" in data:
            data["id"] = data.get("sub")
            if user := await self.get(db=db, id=data.get("id")):
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
