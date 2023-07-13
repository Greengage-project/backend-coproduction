from locale import strcoll
import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi_pagination import Page

import aiofiles
import requests
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.general import deps
from app.sockets import socket_manager 
from app.locales import get_language
from app.general.emails import send_email
from fastapi.responses import FileResponse
from app.models import UserNotification
from app.models import ParticipationRequest
import os
import zipfile
import json
import html

router = APIRouter()


@router.get("", response_model=List[schemas.CoproductionProcessOutFull])
async def list_coproductionprocesses(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    search: str = Query(None)
) -> Any:
    """
    Retrieve coproductionprocesses.
    """
    if not crud.coproductionprocess.can_list(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.coproductionprocess.get_multi_by_user(db, user=current_user, search=search)

@router.get("/public", response_model=Page[Any])
async def list_coproductionprocesses(
    db: Session = Depends(deps.get_db),
    rating: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[List[str]] = Query(None),
    skip: int = 0,
    limit: int = 100,
    language: str = Depends(get_language)

) -> Any:
    """
    Retrieve Public Coproduction Processes.
    """
    # print("search", search)
    # print("rating", rating)
    # print("tag", tag)
    # if not crud.coproductionprocess.can_list(current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.coproductionprocess.get_multi_public(db, search=search,  rating=rating,  language=language, tag=tag)


@router.post("", response_model=schemas.CoproductionProcessOutFull)
async def create_coproductionprocess(
    *,
    db: Session = Depends(deps.get_db),
    coproductionprocess_in: schemas.CoproductionProcessCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new coproductionprocess.
    """
    if not crud.coproductionprocess.can_create(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.coproductionprocess.create(db=db, obj_in=coproductionprocess_in, creator=current_user, set_creator_admin=True)


@router.post("/{id}/logotype", response_model=schemas.CoproductionProcessOutFull)
async def set_logotype(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    file: UploadFile = File(...),
) -> Any:
    if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=id)):
        if crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
            filename, extension = os.path.splitext(file.filename)
            out_file_path = f"/static/coproductionprocesses/{coproductionprocess.id}{extension}"

            async with aiofiles.open("/app" + out_file_path, 'wb') as out_file:
                content = await file.read()  # async read
                await out_file.write(content)  # async write
            return await crud.coproductionprocess.update(db=db, db_obj=coproductionprocess, obj_in=schemas.CoproductionProcessPatch(logotype=out_file_path))
        raise HTTPException(
            status_code=403, detail="You are not allowed to update this coproductionprocess")
    raise HTTPException(status_code=404, detail="Coproduction process not found")


@router.post("/{id}/set_schema", response_model=schemas.CoproductionProcessOutFull)
async def set_schema(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    schema: dict,
) -> Any:
    if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=id)):
        if crud.coproductionprocess.can_update(current_user, coproductionprocess):
            return await crud.coproductionprocess.set_schema(db=db, coproductionschema=schema, coproductionprocess=coproductionprocess)
        raise HTTPException(
            status_code=404, detail="You do not have permissions to update the coproductionprocess")
    raise HTTPException(status_code=404, detail="Coproduction process not found")


@router.post("/{id}/clear_schema", response_model=schemas.CoproductionProcessOutFull)
async def clear_schema(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=id)):
        if crud.coproductionprocess.can_update(current_user, coproductionprocess):
            return await crud.coproductionprocess.clear_schema(db=db, coproductionprocess=coproductionprocess)
        raise HTTPException(
            status_code=404, detail="You do not have permissions to update the coproductionprocess")
    raise HTTPException(status_code=404, detail="Coproduction process not found")



class TeamIn(BaseModel):
    team_id: uuid.UUID


@router.post("/{id}/add_team")
async def add_team(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    team_in: TeamIn,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add team to coproductionprocess (with async default role)
    """
    if coproductionprocess := await crud.coproductionprocess.get(db=db, id=id):
        if team := await crud.team.get(db=db, id=team_in.team_id):
            await crud.coproductionprocess.add_team(
                db=db, coproductionprocess=coproductionprocess, team=team)
            return True
        raise HTTPException(status_code=400, detail="Team not found")
    raise HTTPException(status_code=404, detail="Coproductionprocess not found")

@router.post("/{id}/add_user")
async def add_user(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    user_in: schemas.UserIn,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add user to coproductionprocess (with async default role)
    """
    if coproductionprocess := await crud.coproductionprocess.get(db=db, id=id):
        if user := await crud.user.get(db=db, id=user_in.user_id):
            await crud.coproductionprocess.add_user(
                db=db, coproductionprocess=coproductionprocess, user=user)
            return True
        raise HTTPException(status_code=400, detail="User not found")
    raise HTTPException(status_code=404, detail="Coproductionprocess not found")


@router.put("/{id}", response_model=schemas.CoproductionProcessOutFull)
async def update_coproductionprocess(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    coproductionprocess_in: schemas.CoproductionProcessPatch,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an coproductionprocess.
    """
    
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if coproductionprocess_in.tags:
        tmp_tags = []
        for tag in coproductionprocess_in.tags:
            t = await crud.tag.get(db=db, id=tag['id'])
            tmp_tags.append(t)
        coproductionprocess_in.tags = tmp_tags
        print(coproductionprocess_in.tags)
    return await crud.coproductionprocess.update(
        db=db, db_obj=coproductionprocess, obj_in=coproductionprocess_in)


@router.get("/{id}", response_model=schemas.CoproductionProcessOutFull)
async def read_coproductionprocess(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get coproductionprocess by ID.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_read(db=db, user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return coproductionprocess

@router.get("/public/{id}", response_model=schemas.CoproductionPublicProcessOutFull)
async def read_public_coproductionprocess(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID
) -> Any:
    """
    Get coproductionprocess by ID.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    return coproductionprocess

@router.get("/{id}/catalogue", response_model=schemas.CoproductionProcessOutFull)
async def read_coproductionprocess_catalogue(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get coproductionprocess by ID.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
   
    return coproductionprocess


@router.delete("/{id}")
async def delete_coproductionprocess(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an coproductionprocess.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)

    # If the coproductionprocess is part of a publication it most delete the story first.
    if (coproductionprocess.is_part_of_publication):
        #Delete the story
        story = await crud.story.get_stories_bycopro_catalogue(db=db, coproductionprocess_cloneforpub_id=id,user=current_user)
        if(story):
            await crud.story.remove(db=db, id=story.id)
        
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_remove(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    #Delete all user notification related with this coproduction process
    listUserNotifications=await crud.usernotification.get_user_notifications_by_coproid(db=db,copro_id=id)
    for usernotification in listUserNotifications:
        await crud.usernotification.remove(db=db,id=usernotification.id)

    await crud.coproductionprocess.remove(db=db, id=id)
    return None


# specific

@router.get("/{id}/tree", response_model=Optional[List[schemas.PhaseOutFull]])
async def get_coproductionprocess_tree(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get coproductionprocess tree.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_read(db=db, user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return coproductionprocess.children



# Order the phases by the order of the tasks
def topological_sort(tasks):
    visited = set()
    stack = []
    mapping = {task.name: task for task in tasks}

    def visit(task):
        if task.name not in visited:
            visited.add(task.name)
            for prereq_name in task.prerequisites:
                if prereq_name.name in mapping:
                    visit(mapping[prereq_name.name])
            stack.append(task)

    # Visit tasks without prerequisites first
    for task in tasks:
        if not task.prerequisites:
            visit(task)

    # Then visit the rest
    for task in tasks:
        if task.name not in visited:
            visit(task)

    return stack




#Download the coproduction process in a zip file:

@router.get("/{id}/download")
async def download_zip(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token)
):

    #Get the coproductionprocess tree:
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    #Phases:
    #Order the phases using the topological sort:
    ordered_phases = topological_sort(coproductionprocess.children)
    phase_dict_list = [phase.to_dict() for phase in ordered_phases]

    cont_phases=0
    for phase in ordered_phases:
        ordered_objectives=topological_sort(phase.children)
        objectives_dict_list = [obj.to_dict() for obj in ordered_objectives]
        phase_dict_list[cont_phases]["objectives"]=objectives_dict_list
        
        cont_objectives=0
        for objective in ordered_objectives:
 
            ordered_tasks=topological_sort(objective.children)
            tasks_dict_list = [task.to_dict() for task in ordered_tasks]
            phase_dict_list[cont_phases]["objectives"][cont_objectives]["tasks"]=tasks_dict_list


            cont_objectives=cont_objectives+1

        cont_phases=cont_phases+1
    #print(phase_dict_list)

   
    phases_json = json.dumps(phase_dict_list, indent=2)
    print(phases_json)


    # Define the directory name
    dir_root = 'processes_exported'
    dir_name = dir_root+'/'+coproductionprocess.name.replace(' ', '_')

    # Create the directory if it does not exist
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # Now write the JSON string to a file in the new directory
    with open(os.path.join(dir_name, 'schema.json'), 'w') as f:
        f.write(phases_json)


    # To do a process to download the process information in a file.
    # Convert the CoproductionProcess object to a dictionary
    coproduction_dict = coproductionprocess.to_dict()

    # Specify the directory and filename
    directory = dir_name
    filename = "coproduction.json"

    # Create the full file path
    file_path = os.path.join(directory, filename)

    # Convert the dictionary to JSON
    json_data = json.dumps(coproduction_dict)

    # Write the JSON data to the specified file
    with open(file_path, "w") as json_file:
        json_file.write(json_data)


    # Go through the tasks and download all the files:
    print("-----------------------------------------------------------------")
    for phase in ordered_phases:
        ordered_objectives=topological_sort(phase.children)
        for objective in ordered_objectives:
            ordered_tasks=topological_sort(objective.children)  
            for task in ordered_tasks:
                #Get the assets of this task:
                print("The task is: "+str(task.id))

                assets=await crud.asset.get_multi_withIntData(db, task=task, token=token)
      
                for asset in assets:
                    print("The asset id: "+str(asset.id))
                    print("The asset type: "+str(asset.type))
                    if asset.type=="internalasset":
                        print("The info del internal asset: "+json.dumps(asset.internalData))
                        
                           

                    print(asset)
                    break
                break
            break
        break
    print("-----------------------------------------------------------------")




    # I need to create a json file with the coproduction process
    # specify your directory
    directory = dir_name

    # specify the directory where the zip file will be stored
    zip_directory = 'zipfiles'

    # Check if directory exists. If not, create it.
    if not os.path.exists(zip_directory):
        os.makedirs(zip_directory)

    # specify the name of your zip file
    file_name = coproductionprocess.name.replace(' ', '_')+'.zip'

    # create the full zip file path
    zip_path = os.path.join(zip_directory, file_name)

    zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)

    # compress all files in the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            zipf.write(os.path.join(root, file))

    zipf.close()


    print("The zip file is: "+zip_path)
    return FileResponse(zip_path, media_type='application/zip', filename=file_name)

@router.get("/{id}/tree/catalogue", response_model=Optional[List[schemas.PhaseOutFull]])
async def get_coproductionprocess_tree_catalogue(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get coproductionprocess tree.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
   
    return coproductionprocess.children


# specific

@router.get("/{id}/activity")
async def get_activity(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get coproductionprocess activity.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    return requests.get(f"http://logging/api/v1/log?coproductionprocess_ids={id}&size=20").json()


@router.get("/{id}/assets")
async def read_coproductionprocess_assets(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token)
) -> Any:
    """
    Get coproductionprocess by ID.
    """

    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)

    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_read(db=db, user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    return await crud.coproductionprocess.get_assets(db=db, user=current_user, coproductionprocess=coproductionprocess,token=token)


@router.post("/{id}/administrators")
async def add_administrator(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    user_in: schemas.UserIn,
) -> Any:
    if (user := await crud.user.get(db=db, id=user_in.user_id)):
        if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=id)):
            if crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
                return await crud.coproductionprocess.add_administrator(db=db, db_obj=coproductionprocess, user=user)
            raise HTTPException(
                status_code=403, detail="You are not allowed to update this coproductionprocess")
        raise HTTPException(status_code=404, detail="Coproductionprocess not found")
    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/{id}/administrators/{user_id}")
async def delete_administrator(
    *,
    id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    user_id: str
) -> Any:
    if (user := await crud.user.get(db=db, id=user_id)):
        if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=id)):
            if crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
                return await crud.coproductionprocess.remove_administrator(db=db, db_obj=coproductionprocess, user=user)
            raise HTTPException(
                status_code=403, detail="You are not allowed to update this coproductionprocess")
        raise HTTPException(status_code=404, detail="Coproductionprocess not found")
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/send_message")
async def send_message(
    *,
    id: uuid.UUID,
    message: str
) -> Any:
    await socket_manager.send_to_id(id=id, data={"data": message})


@router.post("/emailApplyToBeContributor")
async def sendEmailApplyToBeContributor(
    *,
    db: Session = Depends(deps.get_db),
    data: dict,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    if (coproductionprocess := await crud.coproductionprocess.get(db=db, id=data["processId"])):
        print("The coproductionprocess is: "+str(coproductionprocess.id))
        
        #Create an request application to be contributor
        newParticipationRequest = ParticipationRequest() 
        newParticipationRequest.candidate_id = current_user.id
        newParticipationRequest.coproductionprocess_id = coproductionprocess.id
        newParticipationRequest.razon=data["razon"]
        db.add(newParticipationRequest)
        db.commit()
        db.refresh(newParticipationRequest)

        
        #Lets create a notification in-app of the solicitude.
        notification = await crud.notification.get_notification_by_event(db=db, event="apply_submited", language=coproductionprocess.language)
        if (notification):
            print("The notification is: "+str(notification.id))
            #I need to create a notification for every admin of the process:
            for admin_id in coproductionprocess.administrators_ids:
                newUserNotification = UserNotification()
                newUserNotification.user_id = admin_id

                newUserNotification.notification_id = notification.id
                newUserNotification.channel = "in_app"
                newUserNotification.state = False
                newUserNotification.coproductionprocess_id = str(
                    coproductionprocess.id)
                newUserNotification.parameters = "{'razon':'"+data["razon"]+"','userName':'"+current_user.full_name+"','userEmail':'"+current_user.email+"','processName':'"+html.escape(
                    coproductionprocess.name)+"','copro_id':'"+str(coproductionprocess.id)+"'}"
            
                print("Create a notification for the user: "+str(admin_id)+" with the notification: "+str(notification.id)+" and the coproductionprocess: "+str(coproductionprocess.id)+" and the parameters: "+str(newUserNotification.parameters))
                db.add(newUserNotification)
                db.commit()
                db.refresh(newUserNotification)


        #if crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        print(data["adminEmails"])
        for admin_email in data["adminEmails"]:
            print("Send email to: "+admin_email)
            send_email(admin_email, "apply_to_be_contributor",
                            {"coprod_id": data["processId"],
                                "user_name": current_user.full_name,
                                "user_email": current_user.email,
                                "coproductionprocess_name": data["coproductionName"],
                                "razon": data["razon"],
                            })

    return "Done"


@router.websocket("/{id}/ws")
async def websocket_endpoint(
    *,
    id: uuid.UUID,
    websocket: WebSocket
):
    await socket_manager.connect(websocket, id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, id)


@router.post("/{id}/copy")
async def copy_coproductionprocess(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.get_current_active_token),
    label_name: str = '',
    from_view:str='',
) -> Any:
    """
    Copy a coproductionprocess.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    
    if(from_view != 'story'):    
        if not crud.coproductionprocess.can_remove(user=current_user, object=coproductionprocess):
            raise HTTPException(status_code=403, detail="Not enough permissions")

    new_coprod = await crud.coproductionprocess.copy(db=db, coproductionprocess=coproductionprocess, user=current_user, token=token, label_name=label_name,from_view=from_view)
    #print("new_coprod", new_coprod)
    if coproductionprocess.logotype:
        filename, extension = os.path.splitext(coproductionprocess.logotype.split('/')[-1])
        in_file_path = coproductionprocess.logotype
        out_file_path = f"/static/coproductionprocesses/{new_coprod.id}{extension}"
        #print("in_file_path", in_file_path)
        
        async with aiofiles.open("/app" + in_file_path, 'rb') as in_file:
            content = await in_file.read()
            #print("content", content)
            async with aiofiles.open("/app" + out_file_path, 'wb') as out_file:
                #print("out_file", out_file_path)
                await out_file.write(content) 
                 # async write
        #print("PREUPDATE")

    
        await crud.coproductionprocess.set_logotype(db=db, coproductionprocess=new_coprod,logotype_path=out_file_path)
    #print("POSTUPDATE")
    # If new_coprod is returned it raises an error regarding recursion with Python
    return new_coprod.id

@router.post("/{id}/addTag")
async def add_tag(
    *,
    db: Session = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
    tag: schemas.Tag,
) -> Any:
    """
    Add tag to coproductionprocess.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await crud.coproductionprocess.add_tag(db=db, db_obj=coproductionprocess, tag=tag)