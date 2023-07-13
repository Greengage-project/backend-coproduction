
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.models import Tag
from app.schemas import TagCreate, TagPatch
from app.general.utils.CRUDBase import CRUDBase


class CRUDTag(CRUDBase[Tag, TagCreate, TagPatch]):
    async def get_by_name(self, db: Session, name: str) -> Optional[Tag]:
        return db.query(Tag).filter(Tag.name == name).first()

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


exportCrud = CRUDTag(Tag, logByDefault=True)
