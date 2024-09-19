from locale import strcoll
import os
import json
import uuid
from typing import Any, Dict, List, Optional

import aiofiles
import requests
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.general import deps
from app.sockets import socket_manager

router = APIRouter()

serviceName = "interlink-gamification-engine"
PATH = "/interlink-gamification/interlink/game"


@router.get("")
async def list_games() -> Any:
    """
    Retrieve games.
    """
    response = requests.get(f"http://{serviceName}{PATH}")
    
    return json.loads(response.text)


@router.get("/{process_id}")
async def get_game(
    *,
    process_id: uuid.UUID,
) -> Any:
    """
    Retrieve game by process_id.
    """
    response = requests.get(f"http://{serviceName}{PATH}/processId/{process_id}")
    
    return response.json()

@router.post("/{process_id}")
async def set_game(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
    taskList: dict
) -> Any:
    """
    Set game by process_id.
    """

    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not taskList:
        raise HTTPException(status_code=400, detail="TaskList not found")
    data = {
        "_id": "null",
        "name": "complexityGame",
        "filename": "game_1.json",
        "tagList": [
                "process1",
                "process3"
        ],
        "taskList": taskList['taskList']

    }
    response = requests.post(f"http://{serviceName}{PATH}/processId/{process_id}",
                             json=data,
                             headers={
                                 'Content-type': 'application/json',
                                 'Accept': '*/*'
                             })

    if response.status_code == 200:
        coproductionprocess.game_id = response.json()['id']
        db.add(coproductionprocess)
        db.commit()
        db.refresh(coproductionprocess)

    return response.text


@router.put("/{process_id}")
async def update_game(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
    task: dict
) -> Any:
    """
    Update game by process_id.
    """

    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    task = task['task']
    game = await get_game(process_id=process_id)
    taskList = game[0]['taskList']
    taskList.append({
        'id': task['id'],
        'management': task['management'],
        'development': task['development'],
        'exploitation': task['exploitation'],
        'completed': False,
        'subtaskList': [],
        'players': []
    })

    data = {
        "active": True,
        "id": coproductionprocess.game_id,
        "name": "complexityGame",
        "processId": str(coproductionprocess.id),
        "filename": "game_1.json",
        "tagList": [
                "process1",
                "process3"
        ],
        "taskList": taskList

    }

    response = requests.put(f"http://{serviceName}{PATH}",
                            json=data,
                            headers={
                                'Content-type': 'application/json',
                                'Accept': '*/*'
                            })

    return response.text


@router.delete("/{process_id}")
async def delete_game(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
) -> Any:
    """
    Delete game by process_id.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    response = requests.delete(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}",
                               headers={
                                   'Content-type': 'application/json',
                                   'Accept': '*/*'
                               })

    return response.text


@router.get("/{process_id}/leaderboard")
async def get_leaderboard(
    *,
    db: Session = Depends(deps.get_db),
    process_id: uuid.UUID,
    # period="global",
) -> Any:
    """
    Get leaderboard by process_id.
    """

    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")

    response = requests.get(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/player/search",
                            params={
                                "period": "global",
                                "activityType": "development",
                            },
                            headers={
                                'Content-type': 'application/json',
                                'Accept': '*/*'
                            })

    return response.json()


@router.get("/{process_id}/{task_id}")
async def get_task(
    *,
    db: Session = Depends(deps.get_db),
    process_id: uuid.UUID,
    task_id: uuid.UUID,
) -> Any:
    """
    Get task by process_id and task_id.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")

    response = requests.get(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}",
                            headers={
                                'Content-type': 'application/json',
                                'Accept': '*/*'
                            })
    return response.json()


@router.put("/{process_id}/{task_id}")
async def update_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
    task_id: uuid.UUID,
    data: dict
) -> Any:
    """
    Update task by process_id and task_id.
    data should be a dict with the following keys:
    - development
    - subtaskList (empty)
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    data['id'] = str(task_id)
    data['subtaskList'] = []

    response = requests.put(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task",
                            json=data,
                            headers={
                                'Content-type': 'application/json',
                                'Accept': '*/*'
                            })

    return response.json()


@router.put("/{process_id}/{task_id}/claim")
async def add_claim(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
    task_id: uuid.UUID,
    data: dict
) -> Any:
    """
    Add claim to game by process_id and task_id.
    data should contain:
    - id
    - name
    - development
    """
    # # print(data.json())
    # json_object = json.dumps(data, indent = 4)
    # print(json_object)
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not await crud.user.get(db=db, id=data['id']):
        raise HTTPException(status_code=404, detail="User not found")

    response = requests.put(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/claim",
                            json=data,
                            headers={
                                'Content-type': 'application/json',
                                'Accept': '*/*'
                            })

    return response.json()


@router.put("/{process_id}/{task_id}/complete")
async def complete_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
    task_id: uuid.UUID,
) -> Any:
    """
    Complete task by process_id and task_id.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    response = requests.put(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/complete",
                            headers={
                                'Content-type': 'application/json',
                                'Accept': '*/*'
                            })

    return response.json()


@router.delete("/{process_id}/{task_id}/revert")
async def revert_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
    task_id: uuid.UUID,
) -> Any:
    """
    Complete task by process_id and task_id.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")
    if not crud.coproductionprocess.can_update(user=current_user, object=coproductionprocess):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Revert claim
    response = requests.put(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/revert",
                            headers={
                                'Content-type': 'application/json',
                                'Accept': '*/*'
                            })

    # Get task
    task = requests.get(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}",
                        headers={
                            'Content-type': 'application/json',
                            'Accept': '*/*'
                        })

    # Delete players
    for player in task.json()['players']:
        data = {
            "development": 0,
            "exploitation": 0,
            "id": player['id'],
            "management": 0,
            "name": "string"
        }
        requests.delete(f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/removePlayer",
                        json=data,
                        headers={
                            'Content-type': 'application/json',
                            'Accept': '*/*'
                        })

    return response.json()
