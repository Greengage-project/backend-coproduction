from app.messages import log
from typing import Any, Dict, Optional, List

from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app.models import Notification, ParticipationRequest, User, Organization
from app.schemas import NotificationCreate, NotificationPatch, ParticipationRequestCreate, ParticipationRequestPatch
import uuid
from app import models
from app.users.crud import exportCrud as users_crud

from sqlalchemy import or_, and_
from fastapi.encoders import jsonable_encoder
from app.sockets import socket_manager
from uuid_by_string import generate_uuid
from app import schemas


class CRUDParticipationRequest(CRUDBase[ParticipationRequest, ParticipationRequestCreate, ParticipationRequestPatch]):
    async def get_multi(self, db: Session, user: User) -> Optional[List[ParticipationRequest]]:
        return db.query(ParticipationRequest).all()

    #Get all notifications by user:
    async def get_participation_requests_by_candidate(self, db: Session, candidate_id: str) -> Optional[List[ParticipationRequest]]:
        listofParticipationRequests = db.query(ParticipationRequest).filter(models.ParticipationRequest.candidate_id==candidate_id).all()
        #print(listofParticipationRequests)
        return listofParticipationRequests
    
    #Get all notifications by coproduction process:
    async def get_inprogress_list_participation_requests_by_copro(self, db: Session, copro_id: str) -> Optional[List[ParticipationRequest]]:

        listofParticipationRequests = db.query(ParticipationRequest).filter(
            ParticipationRequest.coproductionprocess_id==copro_id,
            ParticipationRequest.is_archived.isnot(True)
        ).order_by(ParticipationRequest.created_at.desc()).all()

        return listofParticipationRequests
    
    #Get history (including archived) notifications by coproduction process:
    async def get__full_list_participation_requests_by_copro(self, db: Session, copro_id: str) -> Optional[List[ParticipationRequest]]:

        listofParticipationRequests = db.query(ParticipationRequest).filter(
            ParticipationRequest.coproductionprocess_id==copro_id,
        ).order_by(ParticipationRequest.created_at.desc()).all()

        return listofParticipationRequests


    async def create(self, db: Session, obj_in: ParticipationRequestCreate) -> ParticipationRequest:
        
        obj_in_data = jsonable_encoder(obj_in)
        
        db_obj = ParticipationRequest(**obj_in_data)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        #await socket_manager.broadcast({"event": "participationrequest_created"})

        await self.log_on_create(db_obj)
        return db_obj

    async def update(
        self,
        db: Session,
        db_obj: ParticipationRequest,
        obj_in: schemas.ParticipationRequestPatch
    ) -> ParticipationRequest:
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


exportCrud = CRUDParticipationRequest(ParticipationRequest)