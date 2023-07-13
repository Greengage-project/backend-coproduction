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


@router.get("", response_model=Optional[List[schemas.ParticipationRequestOutFull]])
async def list_participationrequests(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    return await crud.participationrequest.get_multi(db=db, user=current_user)

@router.get("/{candidate_id}/listParticipationRequests", response_model=Optional[List[schemas.ParticipationRequestOutFull]])
async def list_participation_requests(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    candidate_id: str = '',
) -> Any:
    return await crud.participationrequest.get_participation_requests_by_candidate(db=db,candidate_id=candidate_id)

@router.get("/{copro_id}/listFullParticipationRequestsbyCoproId", response_model=Optional[List[schemas.ParticipationRequestOutFull]])
async def list_full_participationrequests_by_copro(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.participationrequest.get__full_list_participation_requests_by_copro(db=db,copro_id=copro_id)


@router.get("/{copro_id}/listInprogressParticipationRequestsbyCoproId", response_model=Optional[List[schemas.ParticipationRequestOutFull]])
async def list_participationrequests_bycopro(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.participationrequest.get_inprogress_list_participation_requests_by_copro(db=db,copro_id=copro_id)


@router.post("", response_model=Optional[schemas.ParticipationRequestOutFull])
async def create_participationrequest(
    *,
    db: Session = Depends(deps.get_db),
    participationrequest_in: schemas.ParticipationRequestCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new participationrequest.
    """
    return await crud.participationrequest.create(db=db, obj_in=participationrequest_in)
    

#Just the Update of the state is cover in the API.
@router.put("/{id}/archive", response_model=Optional[schemas.ParticipationRequestOutFull])
async def archive_participationrequest(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    participationrequest_in: schemas.ParticipationRequestArchive,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an participationrequest.
    """
    participationrequest = await crud.participationrequest.get(db=db, id=id)

    if not participationrequest:
        raise HTTPException(status_code=404, detail="ParticipationRequest not found")
    return await crud.participationrequest.update(db=db, db_obj=participationrequest, obj_in=participationrequest_in)


@router.get("/{id}", response_model=Optional[schemas.ParticipationRequestOutFull])
async def read_participationrequest(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get participationrequest by ID.
    """
    participationrequest = await crud.participationrequest.get(db=db, id=id)
    if not participationrequest:
        raise HTTPException(status_code=404, detail="ParticipationRequest not found")
    return participationrequest



@router.delete("/{id}")
async def delete_participationrequest(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an participationrequest.
    """
    participationrequest = await crud.participationrequest.get(db=db, id=id)
    if not participationrequest:
        raise HTTPException(status_code=404, detail="ParticipationRequest not found")
    return await crud.participationrequest.remove(db=db, id=id)

