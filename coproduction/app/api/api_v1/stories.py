import os
import uuid
from typing import Any, List, Optional

import aiofiles
import json
from fastapi_pagination import Page
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from app import crud, models, schemas
from app.general import deps
from app.models import Story
from typing import Dict,Any
from app.locales import get_language

router = APIRouter()


@router.get("", response_model=Page[Any])
async def list_stories(
    rating: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Optional[dict] = Depends(deps.get_current_user),
    language: str = Depends(get_language)
) -> Any:
    """
    Retrieve stories.
    """
    print("La busqueda es:")
    print(search)
    return await crud.story.get_multiDict(db, search=search,  rating=rating,  language=language)

# @router.get("", response_model=List[schemas.StoryOutFull])
# async def list_storiesbyUser(
#     db: Session = Depends(deps.get_db),
#     current_user: Optional[models.User] = Depends(deps.get_current_active_user),
  
# ) -> Any:
#     return await crud.story.get_multi(db=db, user=current_user)

@router.get("/listStories")
async def list_stories(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
  
) -> Any:
    return await crud.story.get_multi(db=db, user=current_user)


@router.get("/{coproductionprocess_id}/listStories")
async def list_storiesbyCopro(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    coproductionprocess_id: str = '',
) -> Any:
    
    return await crud.story.get_coproductionprocess_stories(db=db,coproductionprocess_id=coproductionprocess_id,user=current_user)



@router.post("", response_model=schemas.StoryOutFull)
async def create_story(
    *,
    db: Session = Depends(deps.get_db),
    story_in: schemas.StoryCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new story.
    """
    # story = await crud.story.get_by_name(db=db, name=story_in.name)
    # if not story:
    return await crud.story.create(db=db, obj_in=story_in)
    # raise HTTPException(status_code=400, detail="Story already exists")


@router.post("/{process_id}/createStory")
async def create_story(
    *,
    db: Session = Depends(deps.get_db),
    story_in: Dict[Any, Any],
    process_id:str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new story.
    """
    print('Llega al metodo create')
    print(story_in)

    newStory=Story()
    newStory.coproductionprocess_id=process_id
    newStory.user_id=current_user.id
    newStory.state=story_in['state']
    newStory.rating=story_in['rating']

    print('Los datos de la historia son:')
    print(story_in['data_story'])


    newStory.data_story=story_in['data_story']

    # story = await crud.story.get_by_name(db=db, name=story_in.name)
    # if not story:
    return await crud.story.create(db=db, obj_in=newStory)
    # raise HTTPException(status_code=400, detail="Story already exists")



@router.put("/{id}", response_model=schemas.StoryOutFull)
async def update_story(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    story_in: schemas.StoryPatch,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an story.
    """
    story = await crud.story.get(db=db, id=id)

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return await crud.story.update(db=db, db_obj=story, obj_in=story_in)



@router.get("/{id}/story")
async def read_story(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get story by ID.
    """
    story = await crud.story.get(db=db, id=id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.delete("/{id}")
async def delete_story(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an story.
    """
    story = await crud.story.get(db=db, id=id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return await crud.story.remove(db=db, id=id)

