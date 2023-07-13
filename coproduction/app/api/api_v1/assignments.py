import os
import uuid
from typing import Any, List, Optional

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from app import crud, models, schemas
from app.general import deps

router = APIRouter()


@router.get("", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_assignments(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    return await crud.assignment.get_multi(db=db, user=current_user)

@router.get("/{user_id}/listAssignments", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_assignments_by_user(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    user_id: str = '',
) -> Any:
    return await crud.assignment.get_assignments_by_user(db=db,user_id=user_id)

@router.get("/{copro_id}/listFullAssignmentsbyCoproId", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_full_assignments_by_copro(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.assignment.get_full_list_assignments_by_coproId(db=db,copro_id=copro_id)

@router.get("/{copro_id}/listFullAssignmentsbyCoproIdUserId", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_full_assignments_by_copro_by_user(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.assignment.get_full_list_assignments_by_coproId_by_userId(db=db,copro_id=copro_id,user_id=current_user.id)

@router.get("/{task_id}/listFullAssignmentsbyTaskId", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_full_assignments_by_task(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    task_id: str = '',
) -> Any:
    return await crud.assignment.get_full_list_assignments_by_taskId(db=db,task_id=task_id)

@router.get("/{asset_id}/listFullAssignmentsbyAssetId", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_full_assignments_by_asset(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    asset_id: str = '',
) -> Any:
    return await crud.assignment.get_full_list_assignments_by_assetId(db=db,asset_id=asset_id)



@router.get("/{assign_id}/view", response_model=Optional[schemas.AssignmentOutFull])
async def list_assignments_bycopro_byassign(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    assign_id: str = '',
) -> Any:
    #Check if the user is assigned to the assignment
    assignment=await crud.assignment.get(db=db,id=uuid.UUID(assign_id))

    print(assignment)

    if not assignment:
        raise HTTPException(
            status_code=400,
            detail="The assignment does not exist",
        )
    
    print(assignment.user_id)
    print(current_user.id)

    if(current_user.id != assignment.user_id):
        raise HTTPException(
            status_code=400,
            detail="The user is not assigned to the assignment",
        )
    return assignment


@router.get("/{copro_id}/listPendingAssignmentsbyCoproId", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_assignments_bycopro(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.assignment.get_pending_list_assignments_by_copro(db=db,copro_id=copro_id)

#Specific for a user:
@router.get("/{copro_id}/listPendingAssignmentsbyCoproIdUserId", response_model=Optional[List[schemas.AssignmentOutFull]])
async def list_assignments_bycopro_byuser(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.assignment.get_pending_list_assignments_by_copro_by_user(db=db,copro_id=copro_id,user_id=current_user.id)


@router.post("", response_model=Optional[schemas.AssignmentOutFull])
async def create_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: schemas.AssignmentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new assignment.
    """
    return await crud.assignment.create(db=db, obj_in=assignment_in)
    
@router.post("/create_user_list", response_model=List[schemas.AssignmentOutFull])
async def create_user_list(
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: schemas.AssignmentCreateUserList,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new assignments from a list.
    """
    assignments = await crud.assignment.create_user_list(db=db, obj_in=assignment_in)
    return assignments


@router.post("/create_team_list", response_model=List[schemas.AssignmentOutFull])
async def create_team_list(
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: schemas.AssignmentCreateTeamList,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new assignments from a list.
    """

    assignments = await crud.assignment.create_team_list(db=db, obj_in=assignment_in)
    return assignments



#Just the Update of the state is cover in the API.
@router.put("/{id}/approve", response_model=Optional[schemas.AssignmentOutFull])
async def archive_assignment(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    assignment_in: schemas.AssignmentApproved,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an assignment.
    """
    assignment = await crud.assignment.get(db=db, id=id)

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return await crud.assignment.update(db=db, db_obj=assignment, obj_in=assignment_in)


@router.get("/{id}", response_model=Optional[schemas.AssignmentOutFull])
async def read_assignment(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get assignment by ID.
    """
    assignment = await crud.assignment.get(db=db, id=id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment



@router.delete("/{id}")
async def delete_assignment(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an assignment.
    """
    assignment = await crud.assignment.get(db=db, id=id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return await crud.assignment.remove(db=db, id=id)

