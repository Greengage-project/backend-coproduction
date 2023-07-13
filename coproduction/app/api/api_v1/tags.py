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


@router.get("")
async def list_tags(
    db: Session = Depends(deps.get_db),
) -> Any:
    return await crud.tag.get_multi(db=db)

@router.post("", response_model=schemas.TagOut)
async def create_tag(
    *,
    db: Session = Depends(deps.get_db),
    tag_in: schemas.TagCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new tag.
    """
    tag = await crud.tag.get_by_name(db=db, name=tag_in.name)
    if not tag:
        return await crud.tag.create(db=db, obj_in=tag_in, creator=current_user)
    raise HTTPException(status_code=400, detail="Tag already exists")

@router.post("/createbyName", response_model=schemas.TagOut)
async def create_tag_by_name(
    *,
    db: Session = Depends(deps.get_db),
    tag_in: schemas.TagCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new tag taking in account the name"""
    tag = await crud.tag.get_by_name(db=db, name=tag_in.name)
    if not tag:
        return await crud.tag.create(db=db, obj_in=tag_in, creator=current_user)
    else:
        return tag


@router.get("/search",  response_model=schemas.TagOut)
async def search_tag(
    name: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Search tag by name.
    """
    tag = await crud.tag.get_by_name(db=db, name=name)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.get("/{id}", response_model=schemas.TagOut)
async def readTag(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get tag by ID.
    """
    tag = await crud.tag.get(db=db, id=id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/{id}")
async def delete_tag(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a tag.
    """
    tag = await crud.tag.get(db=db, id=id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return await crud.tag.remove(db=db, id=id)
