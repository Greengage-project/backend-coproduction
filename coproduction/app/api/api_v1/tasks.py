from typing import Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.general import deps

from app.messages import log

router = APIRouter()

from app.tasks.schemas import *
from app.models import CoproductionProcessNotification
from sqlalchemy import or_, and_


@router.get("", response_model=List[schemas.TaskOut])
async def list_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve tasks.
    """
    if not crud.task.can_list(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    tasks = await crud.task.get_multi(db, skip=skip, limit=limit)
    return tasks


@router.post("", response_model=schemas.TaskOutFull)
async def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: schemas.TaskCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new task.
    """
    if objective := await crud.objective.get(db=db, id=task_in.objective_id):
        if not crud.objective.can_update(current_user, objective):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return await crud.task.create(db=db, obj_in=task_in)
    raise HTTPException(status_code=400, detail="Objective not found")


@router.put("/{id}", response_model=schemas.TaskOutFull)
async def update_task(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    task_in: schemas.TaskPatch,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an task.
    """
    task = await crud.task.get(db=db, id=id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.task.can_update(current_user, task):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.task.update(db=db, db_obj=task, obj_in=task_in)


@router.get("/{id}", response_model=schemas.TaskOutFull)
async def read_task(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get task by ID.
    """
    task = await crud.task.get(db=db, id=id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.task.can_read(current_user, task):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return task


@router.delete("/{id}")
async def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an task.
    """
    task = await crud.task.get(db=db, id=id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.task.can_remove(current_user, task):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    await crud.task.remove(db=db, id=id, user_id=current_user.id)
    return None


#  `/${this.url}/${taskId}/checkTaskAndResource/${resourceId}`
@router.get(
    "/{taskId}/checkTaskAndResource/{resourceId}/{coproductionprocesses}",
    response_model=bool,
)
async def check_task_and_resource(
    *,
    db: Session = Depends(deps.get_db),
    taskId: uuid.UUID,
    resourceId: uuid.UUID,
    coproductionprocesses: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Check if task and resource are related.
    """
    if task := await crud.task.get(db=db, id=taskId):
        # asset should have resourceId as id and taskId as task_id
        resource = await crud.asset.get(db=db, id=resourceId)
        if (
            resource
            and resource.task_id == taskId
            and resource.coproductionprocess_id == coproductionprocesses
        ):
            return True

    return False


@router.get(
    "/{id}/listTaskAssetsContributions", response_model=TaskAssetContributionsOut
)
async def list_task_asset_contributions(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Get all assets contributions
    """

    if task := await crud.task.get(db=db, id=id):

        listofAssets = await crud.asset.get_multi(db=db, task=task)

        # print('El numero de assets is:')
        # print(len(listofAssets))
        listOfAssetsContributions = []
        # Get all assets and all contributions of the each one
        for idx in range(len(listofAssets)):
            # print('El asset es:')
            # print(listofAssets[idx])

            if asset := await crud.asset.get(db=db, id=listofAssets[idx].id):
                # print('Encontro el asset!!')
                # print(asset.id)
                # Get all contribution of users:
                listofContribucionesNotifications = (
                    db.query(CoproductionProcessNotification)
                    .filter(
                        and_(
                            models.CoproductionProcessNotification.asset_id
                            == str(asset.id),
                            models.CoproductionProcessNotification.user_id != None,
                        )
                    )
                    .order_by(models.CoproductionProcessNotification.created_at.desc())
                    .all()
                )

                asset.contributors = listofContribucionesNotifications
                listOfAssetsContributions.append(asset)

        # print('El task es:')
        # print(task)
        task.assetsWithContribution = listOfAssetsContributions
        return task
    raise HTTPException(status_code=404, detail="Task not found")
