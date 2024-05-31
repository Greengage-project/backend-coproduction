from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.general import deps
import requests
from app.sockets import socket_manager 


router = APIRouter()

@router.get("/me", response_model=schemas.UserOutFull)
async def me(
    *,
    db: Session = Depends(deps.get_db),
    token: str = Depends(deps.get_current_active_token)
) -> Any:
    """
    Get or create user.
    """
    cookies = {'auth_token': token}
    response = requests.get(f"http://auth/auth/api/v1/users/me", cookies=cookies, timeout=3)
    return await crud.user.update_or_create(db=db, data=response.json())

@router.get("/search", response_model=List[schemas.UserOutFull])
async def search_user(
    *,
    by: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    organization_id: uuid.UUID = Query(None)
) -> Any:
    """
    Search users
    """
    return await crud.user.search(db=db, user=current_user, organization_id=organization_id, search=by)

@router.post("/send_message")
async def send_message(
    *,
    id: uuid.UUID,
    message: str
) -> Any:
    await socket_manager.send_to_id(id=id, data={"data": message})


@router.websocket("/{id}/ws")
async def websocket_endpoint(
    *,
    id: str,
    websocket: WebSocket
):
    await socket_manager.connect(websocket, id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, id)


@router.put("/agree-terms", response_model=schemas.UserOutFull)
async def agreeTerms(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a user's record to indicate agreement to terms.
    """
    user = await crud.user.get(db=db, id=current_user.id)

    user_patch = {"agreeTermsOfUse": True}
    
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found")
    return await crud.user.update(db=db, db_obj=user, obj_in=user_patch)


@router.put("/refuse-terms", response_model=schemas.UserOutFull)
async def agreeTerms(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a user's record to indicate agreement to terms.
    """
    user = await crud.user.get(db=db, id=current_user.id)

    user_patch = {"agreeTermsOfUse": True}
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found")
    return await crud.user.update(db=db, db_obj=user, obj_in=user_patch)
