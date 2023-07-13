
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.models import Keyword
from app.schemas import KeywordCreate, KeywordPatch
from app.general.utils.CRUDBase import CRUDBase


class CRUDKeyword(CRUDBase[Keyword, KeywordCreate, KeywordPatch]):
    async def get_by_name(self, db: Session, name: str) -> Optional[Keyword]:
        return db.query(Keyword).filter(Keyword.name == name).first()

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


exportCrud = CRUDKeyword(Keyword, logByDefault=True)
