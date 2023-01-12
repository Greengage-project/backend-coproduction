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


@router.get("", response_model=Optional[List[schemas.UserNotificationOutFull]])
async def list_usernotifications(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
  
) -> Any:
    return await crud.usernotification.get_multi(db=db, user=current_user)

@router.get("/{user_id}/listUserNotifications", response_model=Optional[List[schemas.UserNotificationOutFull]])
async def list_usernotifications(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    user_id: str = '',
) -> Any:
    return await crud.usernotification.get_user_notifications(db=db,user_id=user_id)

@router.get("/{user_id}/listUnseenUserNotifications", response_model=Optional[List[schemas.UserNotificationOutFull]])
async def list_unseenusernotifications(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    user_id: str = '',
) -> Any:
    return await crud.usernotification.get_unseen_user_notifications(db=db,user_id=user_id)

#Update the state of all unseen notifications:
@router.get("/setallseen")
async def update_see_allusernotification(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update to seen all usernotification.
    """
    print('The user is the nexxxxt:')
    print(current_user.id)
    await crud.usernotification.set_seen_all_user_notifications(db=db,user_id=current_user.id)
    return {"AllNotifications": True}




# @router.get("/users/{username}", tags=["users"])
# async def read_user(username: str):
#     return {"username": username}

@router.post("", response_model=Optional[schemas.UserNotificationOutFull])
async def create_usernotification(
    *,
    db: Session = Depends(deps.get_db),
    usernotification_in: schemas.UserNotificationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new usernotification.
    """
    # usernotification = await crud.usernotification.get_by_name(db=db, name=usernotification_in.name)
    # if not usernotification:
    return await crud.usernotification.create(db=db, obj_in=usernotification_in)
    # raise HTTPException(status_code=400, detail="UserNotification already exists")



#Just the Update of the state is cover in the API.
@router.put("/{id}", response_model=Optional[schemas.UserNotificationOutFull])
async def update_usernotification(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    usernotification_in: schemas.UserNotificationState,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an usernotification.
    """
    usernotification = await crud.usernotification.get(db=db, id=id)

    if not usernotification:
        raise HTTPException(status_code=404, detail="UserNotification not found")
    return await crud.usernotification.update(db=db, db_obj=usernotification, obj_in=usernotification_in)


@router.get("/{id}", response_model=Optional[schemas.UserNotificationOutFull])
async def read_usernotification(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get usernotification by ID.
    """
    usernotification = await crud.usernotification.get(db=db, id=id)
    if not usernotification:
        raise HTTPException(status_code=404, detail="UserNotification not found")
    return usernotification

@router.get("/{id}/notification")
async def get_usernotification_notification(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get usernotification notification.
    """
    usernotification = await crud.usernotification.get(db=db, id=id)
    notification = await crud.notification.get_notification_by_id(db=db, id=usernotification.notification_id)
    print(notification)
    if not usernotification:
        raise HTTPException(status_code=404, detail="Usernotification not found")
    return notification




@router.delete("/{id}")
async def delete_usernotification(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an usernotification.
    """
    usernotification = await crud.usernotification.get(db=db, id=id)
    if not usernotification:
        raise HTTPException(status_code=404, detail="UserNotification not found")
    return await crud.usernotification.remove(db=db, id=id)

