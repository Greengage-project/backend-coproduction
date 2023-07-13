from app.messages import log
from typing import Any, Dict, Optional, List

from sqlalchemy.orm import Session
from app.general.utils.CRUDBase import CRUDBase
from app.models import Notification, Assignment, User, Organization
from app.schemas import NotificationCreate, NotificationPatch, AssignmentCreate, AssignmentPatch, AssignmentCreateTeamList, AssignmentCreateUserList
import uuid
from app import models
from app.users.crud import exportCrud as users_crud

from sqlalchemy import or_, and_
from fastapi.encoders import jsonable_encoder
from app.sockets import socket_manager
from uuid_by_string import generate_uuid
from app import schemas

from app.teams.crud import exportCrud as teams_crud


class CRUDAssignment(CRUDBase[Assignment, AssignmentCreate, AssignmentPatch]):
    async def get_multi(self, db: Session, user: User) -> Optional[List[Assignment]]:
        return db.query(Assignment).all()

    #Get all notifications by user:
    async def get_assignments_by_user(self, db: Session, user_id: str) -> Optional[List[Assignment]]:
        listofAssignments = db.query(Assignment).filter(models.Assignment.user_id==user_id).all()
        #print(listofAssignments)
        return listofAssignments
    
    #Get all notifications by coproduction process:
    async def get_pending_list_assignments_by_copro(self, db: Session, copro_id: str) -> Optional[List[Assignment]]:

        listofAssignments = db.query(Assignment).filter(
            Assignment.coproductionprocess_id==copro_id,
            Assignment.state.isnot(True)
        ).order_by(Assignment.created_at.desc()).all()

        return listofAssignments
    
    async def get_pending_list_assignments_by_copro_by_user(self, db: Session, copro_id: str, user_id: str) -> Optional[List[Assignment]]:

        listofAssignments = db.query(Assignment).filter(
            Assignment.coproductionprocess_id==copro_id,
            Assignment.user_id==user_id,
            Assignment.state.isnot(True)
        ).order_by(Assignment.created_at.desc()).all()

        return listofAssignments
    
    #Get history (including pending) assignments by coproduction process:
    async def get_full_list_assignments_by_coproId(self, db: Session, copro_id: str) -> Optional[List[Assignment]]:

        listofAssignments = db.query(Assignment).filter(
            Assignment.coproductionprocess_id==copro_id,
        ).order_by(Assignment.created_at.desc()).all()

        return listofAssignments
    
    #Get history (including pending) assignments by coproduction process:
    #For a user
    async def get_full_list_assignments_by_coproId_by_userId(self, db: Session, copro_id: str,user_id) -> Optional[List[Assignment]]:

        listofAssignments = db.query(Assignment).filter(
            Assignment.coproductionprocess_id==copro_id,
            Assignment.user_id==user_id,
        ).order_by(Assignment.created_at.desc()).all()

        return listofAssignments
    
    #Get history (including pending) assignments by coproduction process:
    async def get_full_list_assignments_by_taskId(self, db: Session, task_id: str) -> Optional[List[Assignment]]:

        listofAssignments = db.query(Assignment).filter(
            Assignment.task_id==task_id,
        ).order_by(Assignment.created_at.desc()).all()

        return listofAssignments

    #Get history (including pending) assignments by coproduction process:
    async def get_full_list_assignments_by_assetId(self, db: Session, asset_id: str) -> Optional[List[Assignment]]:

        listofAssignments = db.query(Assignment).filter(
            Assignment.asset_id==asset_id,
        ).order_by(Assignment.created_at.desc()).all()

        return listofAssignments


    async def create(self, db: Session, obj_in: AssignmentCreate) -> Assignment:
        
        obj_in_data = jsonable_encoder(obj_in)
        
        db_obj = Assignment(**obj_in_data)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        #await socket_manager.broadcast({"event": "assignment_created"})

        await self.log_on_create(db_obj)
        return db_obj
    
    async def create_user_list(self, db: Session, obj_in: AssignmentCreateUserList) -> List[Assignment]:
        obj_in_data = jsonable_encoder(obj_in)
        created_assignments = []

        listUsers=obj_in_data['users_id']
        obj_in_data.pop('users_id')

        processed_users = set()  # Store users that have already been processed

        for user_id in listUsers:
            if user_id not in processed_users:  # Only process users that haven't been processed yet
                db_obj = Assignment(**obj_in_data)
                db_obj.user_id = user_id

                db.add(db_obj)
                await self.log_on_create(db_obj)
                created_assignments.append(db_obj)

                processed_users.add(user_id)  # Add the user to the set of processed users

        db.commit()

        for assignment in created_assignments:
            db.refresh(assignment)

        return created_assignments
    
    async def create_team_list(self, db: Session, obj_in: AssignmentCreateTeamList) -> List[Assignment]:
        obj_in_data = jsonable_encoder(obj_in)
        created_assignments = []

        listTeams = obj_in_data['teams_id']
        obj_in_data.pop('teams_id')

        processed_users = set()  # Store users that have already been processed

        for team_id in listTeams:
            team = await teams_crud.get(db, team_id)

            for user in team.users:
                if user.id not in processed_users:  # Only process users that haven't been processed yet
                    db_obj = Assignment(**obj_in_data)
                    db_obj.user_id = user.id

                    db.add(db_obj)
                    await self.log_on_create(db_obj)
                    created_assignments.append(db_obj)

                    processed_users.add(user.id)  # Add the user to the set of processed users

        db.commit()

        for assignment in created_assignments:
            db.refresh(assignment)

        return created_assignments


    async def update(
        self,
        db: Session,
        db_obj: Assignment,
        obj_in: schemas.AssignmentPatch
    ) -> Assignment:
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


exportCrud = CRUDAssignment(Assignment)