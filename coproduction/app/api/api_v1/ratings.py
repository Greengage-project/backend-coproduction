import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
#from app.exceptions import CrudException
from app.general import deps
from fastapi_pagination import Page

router = APIRouter()

@router.get("", response_model=Page[schemas.RatingOut])
async def list_ratings(
    db: Session = Depends(deps.get_db),
    current_user: Optional[dict] = Depends(deps.get_current_user),
    artefact_id: uuid.UUID = Query(None),
) -> Any:
    """
    Retrieve ratings.
    """
    if not crud.rating.can_list(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.rating.get_multi_by_artefact(db, artefact_id=artefact_id)

@router.post("", response_model=schemas.RatingOut)
async def create_rating(
    *,
    db: Session = Depends(deps.get_db),
    rating_in: schemas.RatingCreate,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new rating.
    """
    # if not crud.rating.can_create(current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        ratingCreated=await crud.rating.create(db=db, rating=rating_in, user_id=current_user.id)
        #print('llega hasta aqui Ingresa el primero.')
        #Update rating and ratingCount of story
        if rating_in.artefact_type=="story":
            story=await crud.story.get(db=db, id=rating_in.artefact_id)
            print('Obtiene el story.')
            print(story.id)
            list_ratings=await crud.rating.get_ratting_by_artefacktid(db=db, artefact_id=rating_in.artefact_id)
            print('Obtiene el list_ratings.')
            print(list_ratings)

            sumRating=0
            for(rating) in list_ratings:
                sumRating+=rating.value
            story.rating=sumRating/len(list_ratings)
            story.ratings_count=len(list_ratings)
            print('llega hasta aqui.')
            print(story)
            db.add(story)
            db.commit()
            db.refresh(story)
        
        if rating_in.artefact_type=="publiccoproduction":
            coproductionprocess=await crud.coproductionprocess.get(db=db, id=rating_in.artefact_id)
            list_ratings=await crud.rating.get_ratting_by_artefacktid(db=db, artefact_id=rating_in.artefact_id)
            sumRating=0
            for(rating) in list_ratings:
                sumRating+=rating.value
            coproductionprocess.rating=sumRating/len(list_ratings)
            coproductionprocess.ratings_count=len(list_ratings)
            
            db.add(coproductionprocess)
            db.commit()
            db.refresh(coproductionprocess)

        return ratingCreated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=schemas.RatingOut)
async def update_rating(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    rating_in: schemas.RatingPatch,
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an rating.
    """
    rating = await crud.rating.get(db=db, id=id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if not crud.rating.can_update(current_user, rating):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.rating.update(db=db, db_obj=rating, obj_in=rating_in)


@router.get("/{id}", response_model=schemas.RatingOut)
async def read_rating(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: Optional[dict] = Depends(deps.get_current_user),
) -> Any:
    """
    Get rating by ID.
    """
    rating = await crud.rating.get(db=db, id=id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if not crud.rating.can_read(current_user, rating):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return rating


@router.delete("/{id}", response_model=schemas.RatingOut)
async def delete_rating(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an rating.
    """
    rating = await crud.rating.get(db=db, id=id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if not crud.rating.can_remove(current_user, rating):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    await crud.rating.remove(db=db, id=id)
    return None
