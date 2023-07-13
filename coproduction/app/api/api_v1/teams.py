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


@router.get("", response_model=List[schemas.TeamOutFull])
async def list_teams(
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    organization_id: uuid.UUID = Query(None),
) -> Any:
    if organization_id:
        if organization := await crud.organization.get(db=db, id=id):
            return await crud.team.get_multi(db=db, user=current_user, organization=organization)
        raise HTTPException(
                status_code=404, detail="Organization not found") 
    return await crud.team.get_multi(db=db, user=current_user)


@router.post("", response_model=schemas.TeamOutFull)
async def create_team(
    *,
    db: Session = Depends(deps.get_db),
    team_in: schemas.TeamCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new team.
    """
    teams = await crud.team.get_multi_by_name(db=db, name=team_in.name)
    if teams:
        for team in teams:
            if team.organization_id == team_in.organization_id:
                raise HTTPException(status_code=400, detail="Team already exists")
    
    if team_in.organization_id and await crud.team.can_create(db=db, organization_id=team_in.organization_id, user=current_user):
        #print('LLAMA AL POSR CREATE TEAM!!!!!!!!!!')
        return await crud.team.create(db=db, obj_in=team_in, creator=current_user)
    else:
        raise HTTPException(
            status_code=403, detail="You can not create a team for this organization")
            

@router.post("/{id}/logotype", response_model=schemas.TeamOutFull)
async def set_logotype(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    file: UploadFile = File(...),
) -> Any:
    """
    Create new team.
    """
    if (team := await crud.team.get(db=db, id=id)):
        filename, extension = os.path.splitext(file.filename)
        out_file_path = f"/static/teams/{team.id}{extension}"

        async with aiofiles.open("/app" + out_file_path, 'wb') as out_file:
            content = await file.read()  # async read
            await out_file.write(content)  # async write
        return await crud.team.update(db=db, db_obj=team, obj_in=schemas.TeamPatch(logotype=out_file_path))
    raise HTTPException(status_code=404, detail="Team not found")


class UserIn(BaseModel):
    user_id: str


@router.post("/{id}/users", response_model=schemas.TeamOutFull)
async def add_user(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    user: UserIn
) -> Any:
    """
    Create new team.
    """
    if (team := await crud.team.get(db=db, id=id)):
        if crud.team.can_update(object=team, user=current_user):
            if (user := await crud.user.get(db=db, id=user.user_id)):
                return await crud.team.add_user(db=db, team=team, user=user)
            raise HTTPException(status_code=404, detail="User not found")
        raise HTTPException(status_code=403, detail="You do not have permission")
    raise HTTPException(status_code=404, detail="Team not found")



@router.post("/addtoobservers", response_model=schemas.TeamOutFull)
async def add_to_observers(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    data: schemas.CoproductionProcessAddToObservers
) -> Any:
   
    #Get the coproduction process:
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=data.coproduction_process_id)
    
    #Create Interlink Organization
    #Ask if the organization exists:
    if not (organization := await crud.organization.get_by_name_translations_value(db=db, name_translations='Interlink-Platform')):
        #print('Organization dont exist and is created.')
        #Si no existe la creo:
        obj_in = { 'name_translations': { "en": "Interlink-Platform",
                                          "es": "Interlink-Platform",
                                          "lv": "Interlink-Platform",
                                          "it": "Interlink-Platform" },
                   'logotype': '/static/platform/interlink.jpg',
                   'default_team_type': 'public_administration',
                   'team_creation_permission': 'administrators',
                   'public': False}
        organization = await crud.organization.create(db=db, obj_in=obj_in, creator=coproductionprocess.creator) 


   
    labelTeam = "_".join(coproductionprocess.name.split())


    #Create observers team exists for this coproduction process:
    if not (team := await crud.team.get_by_name(db=db, name='Observers_'+labelTeam)):
        #print('Team Observers for the process dont exist and create it.')
        
        #If it does not exists I create it:
        obj_in = {   'name': 'Observers_'+labelTeam,
                     'description': '',
                     'organization_id': organization.id,
                     'type': 'public_administration',
                     'logotype': '/static/platform/externalTeam.png',
                     'user_ids': []}
        team = await crud.team.create(db=db, obj_in=obj_in, creator=coproductionprocess.creator)

    
    #Add user to observers team:
    if not current_user in team.users:
        #print('Add User to team observers.')
        await crud.team.add_user(db=db, team=team, user=current_user)
    
    #Add permission to the team over the task wehere the assets is:
    if (asset := await crud.asset.get(db=db, id=data.asset_id)):
        print('Asset exists.')
        treeitem = await crud.treeitem.get(db=db, id=asset.task_id)
        
        #Ask if the permission exists:
        if not (permission := await crud.permission.get_for_user_and_treeitem_async(db=db, user=current_user, treeitem=treeitem)):
            print('Permission for this asset dont exist and create it.')
            if(task := await crud.task.get(db=db, id=asset.task_id)):
                #If dont have permission over task create it:
                obj_in = {'access_assets_permission': True,
                        'team_id': team.id,
                        'treeitem_id': task.id,
                        'coproductionprocess_id': coproductionprocess.id}
                
                await crud.permission.create(db=db, obj_in=obj_in, creator=current_user, notifyAfterAdded=False)
                print('Permission created.')

    return team


@router.delete("/{id}/users/{user_id}", response_model=schemas.TeamOutFull)
async def remove_user(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    user_id: str
) -> Any:
    """
    Create new team.
    """
    if (team := await crud.team.get(db=db, id=id)):
        if crud.team.can_update(object=team, user=current_user):
            if (user := await crud.user.get(db=db, id=user_id)):
                return await crud.team.remove_user(db=db, team=team, user=user)
            raise HTTPException(status_code=404, detail="User not found")
        raise HTTPException(status_code=403, detail="You do not have permission")
    raise HTTPException(status_code=404, detail="Team not found")


@router.put("/{id}", response_model=schemas.TeamOutFull)
async def update_team(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    team_in: schemas.TeamPatch,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an team.
    """
    team = await crud.team.get(db=db, id=id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not crud.team.can_update(current_user, team):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.team.update(db=db, db_obj=team, obj_in=team_in)


@router.get("/{id}", response_model=schemas.TeamOutFull)
async def read_team(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_user),
) -> Any:
    """
    Get team by ID.
    """
    team = await crud.team.get(db=db, id=id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not crud.team.can_read(current_user, team):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return team


@router.delete("/{id}")
async def delete_team(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an team.
    """
    team = await crud.team.get(db=db, id=id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not crud.team.can_remove(current_user, team):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.team.remove(db=db, id=id)


@router.post("/{id}/administrators")
async def add_administrator(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    user_in: schemas.UserIn,
) -> Any:
    if (user := await crud.user.get(db=db, id=user_in.user_id)):
        if (team := await crud.team.get(db=db, id=id)):
            if crud.team.can_update(user=current_user, object=team):
                return await crud.team.add_administrator(db=db, db_obj=team, user=user)
            raise HTTPException(
                status_code=403, detail="You are not allowed to update this team")
        raise HTTPException(status_code=404, detail="Team not found")
    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/{id}/administrators/{user_id}")
async def delete_administrator(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    user_id: str
) -> Any:
    if (user := await crud.user.get(db=db, id=user_id)):
        if (team := await crud.team.get(db=db, id=id)):
            if crud.team.can_update(user=current_user, object=team):
                return await crud.team.remove_administrator(db=db, db_obj=team, user=user)
            raise HTTPException(
                status_code=403, detail="You are not allowed to update this team")
        raise HTTPException(status_code=404, detail="Team not found")
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/{id}/apply")
async def add_application(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    if (team := await crud.team.get(db=db, id=id)):
        return await crud.team.add_application(db=db, db_obj=team, user=current_user)
    raise HTTPException(status_code=404, detail="User not found")
