import uuid
from typing import Any, List, Optional

import requests
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.general import deps

from app.messages import log
from app.notificationsManager import notification_manager
from app.assets.schemas import *
from app.models import CoproductionProcessNotification
from sqlalchemy import or_, and_
from app.models import UserNotification

from app.general.emails import send_email, send_team_email

import html

router = APIRouter()


@router.get("", response_model=List[schemas.AssetOutFull])
async def list_assets(
    task_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    # coproductionprocess_id: Optional[uuid.UUID] = Query(None),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve assets.
    """
    # check that task exists
    if not (task := await crud.task.get(db=db, id=task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    if not crud.asset.can_list(db=db, user=current_user, task=task):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return await crud.asset.get_multi(db, task=task)


@router.get("/listAssetswithInternalInfo")
async def list_assets_with_internaldata(
    task_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token)
) -> Any:
    """
    Retrieve assets with public info.
    """
    # check that task exists
    if not (task := await crud.task.get(db=db, id=task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    if not crud.asset.can_list(db=db, user=current_user, task=task):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return await crud.asset.get_multi_withIntData(db, task=task, token=token)


@router.get("/catalogue", response_model=List[schemas.AssetOutFull])
async def list_assets_catalogue(
    task_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    # coproductionprocess_id: Optional[uuid.UUID] = Query(None),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve assets.
    """
    # check that task exists
    if not (task := await crud.task.get(db=db, id=task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    return await crud.asset.get_multi(db, task=task)


def check_interlinker(id, token):
    url = f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{id}"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return response.json()


@router.post("", response_model=schemas.AssetOutFull)
async def create_asset(
    *,
    db: Session = Depends(deps.get_db),
    asset_in: schemas.AssetCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Create new asset.
    """
    # check that task exists
    if not (task := await crud.task.get(db=db, id=asset_in.task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    if not crud.asset.can_create(db=db, user=current_user, task=task):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    #  check that interlinker exists
    if type(asset_in) == schemas.InternalAssetCreate and asset_in.softwareinterlinker_id:
        softwareinterlinker = check_interlinker(asset_in.softwareinterlinker_id, token)

        if asset_in.knowledgeinterlinker_id:
            knowledgeinterlinker = check_interlinker(
                asset_in.knowledgeinterlinker_id, token)

    elif type(asset_in) == schemas.ExternalAssetCreate:
        if asset_in.externalinterlinker_id:
            interlinker = check_interlinker(asset_in.externalinterlinker_id, token)

    return await crud.asset.create(
        db=db, task=task, asset=asset_in, creator=current_user)


class InstantiateSchema(BaseModel):
    knowledgeinterlinker_id: uuid.UUID
    language: str
    task_id: uuid.UUID


@router.post("/instantiate", response_model=schemas.AssetOutFull)
async def instantiate_asset_from_knowledgeinterlinker(
    *,
    asset_in: InstantiateSchema,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Create new asset.
    """
    # first check if task exists
    if not (task := await crud.task.get(db=db, id=asset_in.task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    if not crud.asset.can_create(db=db, user=current_user, task=task):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Gets the knowledge interlinker
    response = requests.get(f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.knowledgeinterlinker_id}", headers={
        "Authorization": "Bearer " + token,
        "Accept-Language": asset_in.language
    })
    interlinker = response.json()

    if response.status_code == 404 or not interlinker:
        raise HTTPException(status_code=404, detail="Knowledge interlinker not found")

    # Clones the genesis asset of the knowledge interlinker by calling the software interlinker's (used by the knowledge) /clone method
    try:
        data_from_interlinker: dict = requests.post(interlinker.get("internal_link") + "/clone", headers={
            "Authorization": "Bearer " + token
        }).json()
    except:
        data_from_interlinker: dict = requests.post(interlinker.get("link") + "/clone", headers={
            "Authorization": "Bearer " + token
        }).json()

    external_asset_id = data_from_interlinker["id"] if "id" in data_from_interlinker else data_from_interlinker["_id"]
    # Creates an InternalAsset object with reference to the software interlinker that manages the asset, the knowledge interlinker that contained the genesis asset id and the id of the external resource
    return await crud.asset.create(db=db, task=task, creator=current_user, asset=schemas.InternalAssetCreate(
        **{
            "knowledgeinterlinker_id": asset_in.knowledgeinterlinker_id,
            "type": "internalasset",
            "softwareinterlinker_id": interlinker.get("softwareinterlinker_id"),
            "external_asset_id": external_asset_id,
            "task_id": task.id
        }
    ))


@router.post("/{id}/clone", response_model=schemas.AssetOutFull)
async def clone_asset(
    *,
    id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Clone asset.
    """
    asset: models.Asset
    if not (asset := await crud.asset.get(db=db, id=id)):
        raise HTTPException(status_code=404, detail="Asset not found")

    # first check if task exists
    task: models.Task
    if not (task := await crud.task.get(db=db, id=asset.task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    if not crud.asset.can_create(db=db, user=current_user, task=task):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # TODO: check that the software interlinker of the original asset has the clone capability
    if asset.type == "internalasset":
        try:
            data_from_interlinker = requests.post(asset.internal_link + "/clone", headers={
                "Authorization": "Bearer " + token
            }).json()
        except:
            data_from_interlinker = requests.post(asset.link + "/clone", headers={
                "Authorization": "Bearer " + token
            }).json()

        external_asset_id = data_from_interlinker["id"] if "id" in data_from_interlinker else data_from_interlinker["_id"]

        asset: models.InternalAsset
        db_asset = await crud.asset.create(db=db, task=task, asset=schemas.InternalAssetCreate(
            task_id=asset.task_id,
            softwareinterlinker_id=asset.softwareinterlinker_id,
            knowledgeinterlinker_id=asset.knowledgeinterlinker_id,
            external_asset_id=external_asset_id
        ), creator=current_user)

    elif asset.type == "externalasset":
        asset: models.ExternalAsset
        db_asset = await crud.asset.create(db=db, task=task, asset=schemas.ExternalAssetCreate(
            task_id=asset.task_id,
            externalinterlinker_id=asset.externalinterlinker_id,
            name=asset.name,
            uri=asset.uri
        ), creator=current_user)

    else:
        raise HTTPException(status_code=500, detail="Asset type not recognized")

    return db_asset


@router.post("/emailAskTeamContribution")
async def create_copro_notification(
    *,
    db: Session = Depends(deps.get_db),
    data: EmailAssetContribution,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    print(data)
    print(data.processId)
    if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=data.processId)):
        if crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
            for team_id in data.listTeams:
                if (team := await crud.team.get(db=db, id=team_id)):

                    for user_id in team.user_ids:
                        if (user := await crud.user.get(db=db, id=user_id)):
                             #Lets create a notification in-app of the solicitude.
                            notification = await crud.notification.get_notification_by_event(db=db, event="assign_resource", language=coproductionprocess.language)
                            if (notification):


                                newUserNotification = UserNotification()
                                newUserNotification.user_id = user.id

                                newUserNotification.notification_id = notification.id
                                newUserNotification.channel = "in_app"
                                newUserNotification.state = False
                                newUserNotification.coproductionprocess_id = str(
                                    coproductionprocess.id)
                                newUserNotification.parameters = "{'resourceName':'"+data.asset_name+"','taskName':'"+data.taskName+"','resourceId':'"+str(data.resourceId)+"','processName':'"+html.escape(
                                    coproductionprocess.name)+"','coproId':'"+str(coproductionprocess.id)+"'}"

                                
                                db.add(newUserNotification)
                                db.commit()
                                db.refresh(newUserNotification)





                    send_team_email(team, "ask_team_contribution",
                                    {"link": data.link,
                                     "icon_link": data.icon,
                                     "instructions": data.instructions,
                                     "asset_name": data.asset_name,
                                     "subject": data.subject
                                     })

    return "Done"


@router.post("/emailAskUserContribution")
async def create_user_copro_notification(
    *,
    db: Session = Depends(deps.get_db),
    data: EmailUserAssetContribution,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    print(data)
    print(data.processId)
    if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=data.processId)):
        if crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        
            if (user := await crud.user.get(db=db, id=data.userTo)):

                #Lets create a notification in-app of the solicitude.
                notification = await crud.notification.get_notification_by_event(db=db, event="assign_resource", language=coproductionprocess.language)
                if (notification):


                    newUserNotification = UserNotification()
                    newUserNotification.user_id = user.id

                    newUserNotification.notification_id = notification.id
                    newUserNotification.channel = "in_app"
                    newUserNotification.state = False
                    newUserNotification.coproductionprocess_id = str(
                        coproductionprocess.id)
                    newUserNotification.parameters = "{'resourceName':'"+data.asset_name+"','taskName':'"+data.taskName+"','resourceId':'"+str(data.resourceId)+"','processName':'"+html.escape(
                        coproductionprocess.name)+"','coproId':'"+str(coproductionprocess.id)+"'}"

                    
                    db.add(newUserNotification)
                    db.commit()
                    db.refresh(newUserNotification)




                #Send email to user

                send_email(user.email, "ask_team_contribution",
                                {"link": data.link,
                                    "icon_link": data.icon,
                                    "instructions": data.instructions,
                                    "asset_name": data.asset_name,
                                    "subject": data.subject
                                    })

    return "Done"


@router.put("/{id}", response_model=schemas.AssetOutFull)
async def update_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    asset_in: schemas.AssetPatch,
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Update an asset.
    """
    asset = await crud.asset.get(db=db, id=id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not crud.asset.can_update(db=db, user=current_user, task=asset.task):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.asset.update(db=db, db_obj=asset, obj_in=asset_in)


@router.get("/{id}", response_model=schemas.AssetOutFull)
async def read_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Get asset by ID.
    """

    if asset := await crud.asset.get(db=db, id=id):
        if not crud.asset.can_read(db, current_user, asset.task):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return asset
    raise HTTPException(status_code=404, detail="Asset not found")


@router.get("/{id}/listContributions", response_model=AssetOutContributions)
async def read_asset_contributions(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Get all assets contributions
    """

    if asset := await crud.asset.get(db=db, id=id):
        # Get all contribution of users:
        listofContribucionesNotifications = db.query(CoproductionProcessNotification).filter(and_(
            models.CoproductionProcessNotification.asset_id == str(asset.id),
            models.CoproductionProcessNotification.user_id != None
        )
        ).order_by(models.CoproductionProcessNotification.created_at.desc()).all()

        asset.contributors = listofContribucionesNotifications
        return asset
    raise HTTPException(status_code=404, detail="Asset not found")


@router.get("/internal/{id}")
async def read_internal_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    token: str = Depends(deps.get_current_active_token),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get asset by ID.
    """

    if asset := await crud.asset.get(db=db, id=id):
        if asset.type == "internalasset":
            if not crud.asset.can_read(db=db, user=current_user, task=asset.task):
                raise HTTPException(status_code=403, detail="Not enough permissions")

            # print("Retrieving internal ", asset.link)
            await log(crud.asset.enrich_log_data(asset, {
                "action": "GET"
            }))
            try:
                return requests.get(asset.internal_link, headers={
                    "Authorization": "Bearer " + token
                }).json()
            except:
                return requests.get(asset.link, headers={
                    "Authorization": "Bearer " + token
                }).json()
        raise HTTPException(status_code=400, detail="Asset is not internal")
    raise HTTPException(status_code=404, detail="Asset not found")


@router.get("/internal/{id}/catalogue")
async def read_internal_asset_catalogue(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    token: str = Depends(deps.get_current_active_token),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get asset by ID.
    """

    if asset := await crud.asset.get(db=db, id=id):
        if asset.type == "internalasset":
            # if not crud.asset.can_read(db=db, user=current_user, task=asset.task):
            #     raise HTTPException(status_code=403, detail="Not enough permissions")

            # print("Retrieving internal ", asset.link)
            await log(crud.asset.enrich_log_data(asset, {
                "action": "GET"
            }))
            try:
                return requests.get(asset.internal_link, headers={
                    "Authorization": "Bearer " + token
                }).json()
            except:
                return requests.get(asset.link, headers={
                    "Authorization": "Bearer " + token
                }).json()
        raise HTTPException(status_code=400, detail="Asset is not internal")
    raise HTTPException(status_code=404, detail="Asset not found")


@router.delete("/{id}")
async def delete_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Delete an asset.
    """

    if asset := await crud.asset.get(db=db, id=id):
        if not crud.asset.can_remove(db=db, user=current_user, task=asset.task):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        # Erase all notification related with this asset.
        listNotificationbyAsset = await crud.coproductionprocessnotification.get_coproductionprocess_notifications_justbyAseetId(db=db, asset_id=str(asset.id))
        for notification in listNotificationbyAsset:
            db.delete(notification)
        db.commit()

        await crud.asset.remove(db=db, id=id)
        return None

    # TODO: DELETE to interlinker
    raise HTTPException(status_code=404, detail="Asset not found")
