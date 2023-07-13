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


@router.get("", response_model=Optional[List[schemas.ClaimOutFull]])
async def list_claims(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    return await crud.claim.get_multi(db=db, user=current_user)

@router.get("/{user_id}/listClaims", response_model=Optional[List[schemas.ClaimOutFull]])
async def list_claims_by_user(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    user_id: str = '',
) -> Any:
    return await crud.claim.get_claims_by_user(db=db,user_id=user_id)

@router.get("/{copro_id}/listFullClaimsbyCoproId", response_model=Optional[List[schemas.ClaimOutFull]])
async def list_full_claims_by_copro(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.claim.get_full_list_claims_by_coproId(db=db,copro_id=copro_id)

@router.get("/{task_id}/listFullClaimsbyTaskId", response_model=Optional[List[schemas.ClaimOutFull]])
async def list_full_claims_by_task(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    task_id: str = '',
) -> Any:
    return await crud.claim.get_full_list_claims_by_taskId(db=db,task_id=task_id)

@router.get("/{asset_id}/listFullClaimsbyAssetId", response_model=Optional[List[schemas.ClaimOutFull]])
async def list_full_claims_by_asset(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    asset_id: str = '',
) -> Any:
    return await crud.claim.get_full_list_claims_by_assetId(db=db,asset_id=asset_id)



@router.get("/{copro_id}/listPendingClaimsbyCoproId", response_model=Optional[List[schemas.ClaimOutFull]])
async def list_claims_bycopro(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    copro_id: str = '',
) -> Any:
    return await crud.claim.get_pending_list_claims_by_copro(db=db,copro_id=copro_id)


@router.post("", response_model=Optional[schemas.ClaimOutFull])
async def create_claim(
    *,
    db: Session = Depends(deps.get_db),
    claim_in: schemas.ClaimCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new claim.
    """
    return await crud.claim.create(db=db, obj_in=claim_in)
    
@router.post("/create_user_list", response_model=List[schemas.ClaimOutFull])
async def create_user_list(
    *,
    db: Session = Depends(deps.get_db),
    claim_in: schemas.ClaimCreateUserList,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new claims from a list.
    """
    claims = await crud.claim.create_user_list(db=db, obj_in=claim_in)
    return claims


@router.post("/create_team_list", response_model=List[schemas.ClaimOutFull])
async def create_team_list(
    *,
    db: Session = Depends(deps.get_db),
    claim_in: schemas.ClaimCreateTeamList,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new claims from a list.
    """

    claims = await crud.claim.create_team_list(db=db, obj_in=claim_in)
    return claims



#Just the Update of the state is cover in the API.
@router.put("/{id}/approve", response_model=Optional[schemas.ClaimOutFull])
async def archive_claim(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    claim_in: schemas.ClaimApproved,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an claim.
    """
    claim = await crud.claim.get(db=db, id=id)

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return await crud.claim.update(db=db, db_obj=claim, obj_in=claim_in)


@router.get("/{id}", response_model=Optional[schemas.ClaimOutFull])
async def read_claim(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get claim by ID.
    """
    claim = await crud.claim.get(db=db, id=id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim



@router.delete("/{id}")
async def delete_claim(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an claim.
    """
    claim = await crud.claim.get(db=db, id=id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return await crud.claim.remove(db=db, id=id)

