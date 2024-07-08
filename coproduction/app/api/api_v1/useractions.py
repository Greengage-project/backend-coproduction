from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.general import deps
import requests

router = APIRouter()


@router.post("/action", response_model=schemas.UserActionOut)
async def create_user_action(
    *,
    db: Session = Depends(deps.get_db),
    token: str = Depends(deps.get_current_active_token),
    useraction_in: schemas.UserActionCreateBody
) -> Any:
    """
    Get or create user.
    """
    cookies = {'auth_token': token}
    response = requests.get(f"http://auth/auth/api/v1/users/me",
                            cookies=cookies, timeout=3)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code,
                            detail=response.json())

    user_id = response.json().get('id')
    new_useraction = schemas.UserActionCreate(
        **useraction_in.dict(), user_id=user_id)
    response_useraction = await crud.useraction.create(
        db=db, obj_in=new_useraction)

    return response_useraction
