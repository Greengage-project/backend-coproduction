import uuid
from typing import Any, List, Optional

import requests
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.general import deps
from fastapi.encoders import jsonable_encoder

from app.messages import log

router = APIRouter()


@router.get("", response_model=List[schemas.AssetOutFull])
async def list_assets(
    db: Session = Depends(deps.get_db),
    coproductionprocess_id: Optional[uuid.UUID] = Query(None),
    task_id: Optional[uuid.UUID] = Query(None),
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve assets.
    """

    if not crud.asset.can_list(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset = await crud.asset.get_multi_filtered(db, task_id=task_id, coproductionprocess_id=coproductionprocess_id)

    return asset


@router.post("", response_model=schemas.AssetOutFull)
async def create_asset(
    *,
    db: Session = Depends(deps.get_db),
    asset_in: schemas.AssetCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new asset.
    """


    if not crud.asset.can_create(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # first check if task exists
    if not (task := await crud.task.get(db=db, id=asset_in.task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    # check that interlinker in catalogue
    try:
        url = None
        if type(asset_in) == schemas.InternalAssetCreate and asset_in.softwareinterlinker_id:
            url = f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.softwareinterlinker_id}"

        elif type(asset_in) == schemas.ExternalAssetCreate and asset_in.externalinterlinker_id:
            url = f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.externalinterlinker_id}"

        response = requests.get(url, headers={
            "X-API-Key": "secret"
        })
        print("CREATING WITH ", response.json())
        assert response.status_code == 200

        interlinker = response.json()

    except Exception as e:
        raise e

    asset = await crud.asset.create(
        db=db, asset=asset_in, coproductionprocess_id=task.objective.phase.coproductionprocess_id, creator=current_user)

    # my post create new asset
    await log({
        "model": "ASSET",
        "action": "CREATE",
        "crud": False,
        "coproductionprocess_id": asset.task.objective.phase.coproductionprocess_id,
        "phase_id": asset.task.objective.phase_id,
        "objective_id": asset.task.objective_id,
        "task_id": asset.task_id,
        "asset_id": asset.id,
        "knowledgeinterlinker_id": "",
        "knowledgeinterlinker_name": "",
        "softwareinterlinker_id": interlinker.get("id"),
        "softwareinterlinker_name": interlinker.get("name")
    })

    return asset

class InstantiateSchema(BaseModel):
    knowledgeinterlinker_id: uuid.UUID
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
    if not crud.asset.can_create(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # first check if task exists
    if not (task := await crud.task.get(db=db, id=asset_in.task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    # TODO: check if interlinker can clone
    response = requests.get(f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.knowledgeinterlinker_id}", headers={
                "X-API-Key": "secret"
            })
    interlinker = response.json()

    if response.status_code == 404 or not interlinker:
        raise HTTPException(status_code=404, detail="Knowledge interlinker not found")

    try:
        external_info : dict = requests.post(interlinker.get("internal_link") + "/clone", headers={
            "Authorization": "Bearer " + token
        }).json()
    except:
        external_info : dict = requests.post(interlinker.get("link") + "/clone", headers={
            "Authorization": "Bearer " + token
        }).json()
    asset = await crud.asset.create(db=db, coproductionprocess_id=task.objective.phase.coproductionprocess_id, creator=current_user, asset=schemas.InternalAssetCreate(
        **{
            "knowledgeinterlinker_id": asset_in.knowledgeinterlinker_id,
            "type": "internalasset",
            "softwareinterlinker_id": interlinker.get("softwareinterlinker_id"),
            "external_asset_id": external_info.get("id") or external_info.get("_id"),
            "task_id": task.id
        }
    ))

    # my post create new asset from template
    await log({
        "model": "ASSET",
        "action": "CREATE",
        "crud": False,
        "coproductionprocess_id": asset.task.objective.phase.coproductionprocess_id,
        "phase_id": asset.task.objective.phase_id,
        "objective_id": asset.task.objective_id,
        "task_id": asset.task_id,
        "asset_id": asset.id,
        "knowledgeinterlinker_id": asset.knowledgeinterlinker_id,
        "knowledgeinterlinker_name": interlinker.get("name"),
        "softwareinterlinker_id": interlinker.get("softwareinterlinker").get("id"),
        "softwareinterlinker_name": interlinker.get("softwareinterlinker").get("name")
    })

    return asset


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
    if not crud.asset.can_create(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset : models.Asset
    if not (asset := await crud.asset.get(db=db, id=id)):
        raise HTTPException(status_code=404, detail="Asset not found")

    # first check if task exists
    task : models.Task
    if not (task := await crud.task.get(db=db, id=asset.task_id)):
        raise HTTPException(status_code=404, detail="Task not found")

    if asset.type == "internalasset":
        try:
            external_info = requests.post(asset.internal_link + "/clone", headers={
                "Authorization": "Bearer " + token
            }).json()
        except:
            external_info = requests.post(asset.link + "/clone", headers={
                "Authorization": "Bearer " + token
            }).json()

        external_id = external_info["id"] if "id" in external_info else external_info["_id"]

        asset : models.InternalAsset
        return await crud.asset.create(db=db, asset=schemas.InternalAssetCreate(
            task_id=asset.task_id,
            softwareinterlinker_id=asset.softwareinterlinker_id,
            knowledgeinterlinker_id=asset.knowledgeinterlinker_id,
            external_asset_id=external_id
        ), coproductionprocess_id=task.objective.phase.coproductionprocess_id, creator=current_user)

    if asset.type == "externalasset":
        asset : models.ExternalAsset
        return await crud.asset.create(db=db, asset=schemas.ExternalAssetCreate(
            task_id=asset.task_id,
            externalinterlinker_id=asset.externalinterlinker_id,
            name=asset.name,
            uri=asset.uri
        ), coproductionprocess_id=task.objective.phase.coproductionprocess_id, creator=current_user)
    raise HTTPException(status_code=500, detail="Asset type not recognized")

@router.put("/{id}", response_model=schemas.AssetOutFull)
async def update_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    asset_in: schemas.AssetPatch,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an asset.
    """
    asset = await crud.asset.get(db=db, id=id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not crud.asset.can_update(current_user, asset):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    asset = await crud.asset.update(db=db, db_obj=asset, obj_in=asset_in)


    # check that interlinker in catalogue
    try:
        if type(asset_in) == schemas.InternalAssetCreate and asset_in.softwareinterlinker_id:
            response = requests.get(f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.softwareinterlinker_id}", headers={
                "X-API-Key": "secret"
            })
            print("CREATING WITH ", response.json())
            assert response.status_code == 200
        if type(asset_in) == schemas.ExternalAssetCreate and asset_in.externalinterlinker_id:
            response = requests.get(f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.externalinterlinker_id}", headers={
                "X-API-Key": "secret"
            })
            print("CREATING WITH ", response.json())
            assert response.status_code == 200

        interlinker = response.json()

    except Exception as e:
        raise e

    # my put
    await log({
        "model": "ASSET",
        "action": "UPDATE",
        "crud": False,
        "coproductionprocess_id": asset.task.objective.phase.coproductionprocess_id,
        "phase_id": asset.task.objective.phase_id,
        "objective_id": asset.task.objective_id,
        "task_id": asset.task_id,
        "asset_id": asset.id,
        "knowledgeinterlinker_id": asset.knowledgeinterlinker_id,
        "knowledgeinterlinker_name": interlinker.get("name"),
        "softwareinterlinker_id": interlinker.get("softwareinterlinker").get("id"),
        "softwareinterlinker_name": interlinker.get("softwareinterlinker").get("name")
    })

    return asset


@router.get("/{id}", response_model=schemas.AssetOutFull)
async def read_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    asset_in: schemas.AssetPatch,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get asset by ID.
    """
    
    if asset := await crud.asset.get(db=db, id=id):
        if not crud.asset.can_read(current_user, asset):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        #  check that interlinker in catalogue
        try:
            if type(asset_in) == schemas.InternalAssetCreate and asset_in.softwareinterlinker_id:
                response = requests.get(
                    f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.softwareinterlinker_id}",
                    headers={
                        "X-API-Key": "secret"
                    })
                print("CREATING WITH ", response.json())
                assert response.status_code == 200
            if type(asset_in) == schemas.ExternalAssetCreate and asset_in.externalinterlinker_id:
                response = requests.get(
                    f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.externalinterlinker_id}",
                    headers={
                        "X-API-Key": "secret"
                    })
                print("CREATING WITH ", response.json())
                assert response.status_code == 200

            interlinker = response.json()

        except Exception as e:
            raise e

        # my get
        await log({
            "model": "ASSET",
            "action": "GET",
            "crud": False,
            "coproductionprocess_id": asset.task.objective.phase.coproductionprocess_id,
            "phase_id": asset.task.objective.phase_id,
            "objective_id": asset.task.objective_id,
            "task_id": asset.task_id,
            "asset_id": asset.id,
            "knowledgeinterlinker_id": asset.knowledgeinterlinker_id,
            "knowledgeinterlinker_name": interlinker.get("name"),
            "softwareinterlinker_id": interlinker.get("softwareinterlinker").get("id"),
            "softwareinterlinker_name": interlinker.get("softwareinterlinker").get("name")
        })

        return asset

    raise HTTPException(status_code=404, detail="Asset not found")

@router.get("/internal/{id}")
async def read_internal_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    token: str = Depends(deps.get_current_active_token),
) -> Any:
    """
    Get asset by ID.
    """
    
    if asset := await crud.asset.get(db=db, id=id):
        if asset.type == "internalasset":
            print("Retrieving internal ", asset.link)
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


@router.delete("/{id}", response_model=schemas.AssetOutFull)
async def delete_asset(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    asset_in: schemas.AssetPatch,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an asset.
    """

    if asset := await crud.asset.get(db=db, id=id):
        if not crud.asset.can_remove(current_user, asset):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        await log({
            "model": "ASSET",
            "action": "DELETE",
            "crud": False,
            "coproductionprocess_id": asset.task.objective.phase.coproductionprocess_id,
            "phase_id": asset.task.objective.phase_id,
            "objective_id": asset.task.objective_id,
            "task_id": asset.task_id,
            "asset_id": asset.id,
            "interlinker_id": asset.softwareinterlinker_id
        })
        await crud.asset.remove(db=db, id=id)


        #  check that interlinker in catalogue
        try:
            if type(asset_in) == schemas.InternalAssetCreate and asset_in.softwareinterlinker_id:
                response = requests.get(
                    f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.softwareinterlinker_id}",
                    headers={
                        "X-API-Key": "secret"
                    })
                print("CREATING WITH ", response.json())
                assert response.status_code == 200
            if type(asset_in) == schemas.ExternalAssetCreate and asset_in.externalinterlinker_id:
                response = requests.get(
                    f"http://{settings.CATALOGUE_SERVICE}/api/v1/interlinkers/{asset_in.externalinterlinker_id}",
                    headers={
                        "X-API-Key": "secret"
                    })
                print("CREATING WITH ", response.json())
                assert response.status_code == 200

            interlinker = response.json()

        except Exception as e:
            raise e

        # my delete
        await log({
            "model": "ASSET",
            "action": "DELETE",
            "crud": False,
            "coproductionprocess_id": asset.task.objective.phase.coproductionprocess_id,
            "phase_id": asset.task.objective.phase_id,
            "objective_id": asset.task.objective_id,
            "task_id": asset.task_id,
            "asset_id": asset.id,
            "knowledgeinterlinker_id": asset.knowledgeinterlinker_id,
            "knowledgeinterlinker_name": interlinker.get("name"),
            "softwareinterlinker_id": interlinker.get("softwareinterlinker").get("id"),
            "softwareinterlinker_name": interlinker.get("softwareinterlinker").get("name")
        })

        return None

    # TODO: DELETE to interlinker
    raise HTTPException(status_code=404, detail="Asset not found")
