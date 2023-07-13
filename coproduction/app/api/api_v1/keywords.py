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
async def list_keywords(
    db: Session = Depends(deps.get_db),
) -> Any:
    return await crud.keyword.get_multi(db=db)

@router.post("", response_model=schemas.KeywordOut)
async def create_keyword(
    *,
    db: Session = Depends(deps.get_db),
    keyword_in: schemas.KeywordCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new keyword.
    """
    keyword = await crud.keyword.get_by_name(db=db, name=keyword_in.name)
    if not keyword:
        return await crud.keyword.create(db=db, obj_in=keyword_in, creator=current_user)
    raise HTTPException(status_code=400, detail="Keyword already exists")

@router.post("/createbyName", response_model=schemas.KeywordOut)
async def create_keyword_by_name(
    *,
    db: Session = Depends(deps.get_db),
    keyword_in: schemas.KeywordCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new keyword taking in account the name"""
    keyword = await crud.keyword.get_by_name(db=db, name=keyword_in.name)
    if not keyword:
        return await crud.keyword.create(db=db, obj_in=keyword_in, creator=current_user)
    else:
        return keyword


@router.get("/search",  response_model=schemas.KeywordOut)
async def search_keyword(
    name: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Search keyword by name.
    """
    keyword = await crud.keyword.get_by_name(db=db, name=name)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword

@router.get("/{id}", response_model=schemas.KeywordOut)
async def readKeyword(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get keyword by ID.
    """
    keyword = await crud.keyword.get(db=db, id=id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.delete("/{id}")
async def delete_keyword(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a keyword.
    """
    keyword = await crud.keyword.get(db=db, id=id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return await crud.keyword.remove(db=db, id=id)
