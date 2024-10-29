from locale import strcoll
import os
import json
import uuid
from typing import Any, Dict, List, Optional

import aiofiles
import requests
from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.general import deps
from app.sockets import socket_manager
from app.config import settings

router = APIRouter()

service_name = settings.NEW_GAMIFICATION_SERVICE_NAME
api_key = settings.NEW_GAMIFICATION_API_KEY

# def get_game_config(response, coproductionprocess):
#     """
#     Retrieves the game configuration for the given coproduction process.
#     If any exception occurs, fallback values are used.

#     Args:
#         response: The response from the gamification engine.
#         coproductionprocess: The object containing the game configuration.

#     Returns:
#         dict: A dictionary containing game strategy and gamification engine.
#     """

#     default_response = {
#         "game_strategy": "declarative",
#         "game_gamification_engine": "old_gamification",
#     }

#     response.update(default_response)
#     try:
#         response["game_strategy"] = coproductionprocess.game_strategy
#         response["game_gamification_engine"] = (
#             coproductionprocess.game_gamification_engine
#         )
#     except AttributeError as e:
#         pass
#     return response


@router.get("")
async def list_games() -> Any:
    """
    Retrieve games.
    """

    response = requests.get(
        f"http://{service_name}games", headers={"X-API-Key": api_key}
    )
    return json.loads(response.text)


@router.get("/{process_id}")
async def get_game(
    *,
    db: Session = Depends(deps.get_db),
    process_id: uuid.UUID,
) -> Any:
    """
    Retrieve game by process_id.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    response = requests.get(f"http://{serviceName}{PATH}/processId/{process_id}").json()

    print("-----------------------------------")
    print("New - GET GAME")
    print("New - GET GAME")
    print("New - GET GAME")
    print("New - GET GAME")
    print("New - GET GAME")
    print(response)
    print("-----------------------------------")
    return response


@router.post("/{process_id}")
async def set_game(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    process_id: uuid.UUID,
    taskList: dict,
) -> Any:
    """
    Set game by process_id.
    """

    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not crud.coproductionprocess.can_update(
        user=current_user, object=coproductionprocess
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not taskList:
        raise HTTPException(status_code=400, detail="TaskList not found")

    # create game

    create_game_body = {
        "externalGameId": str(process_id),
        "platform": "GREENGAGE",
        "strategyId": "greengageStrategy",
        "params": [],
    }
    external_gameId = None
    try:
        response = requests.post(
            f"http://{service_name}games",
            json=create_game_body,
            headers={"X-API-Key": api_key},
        )

        if (
            response.status_code == 409
            and "Game already exists with externalGameId"
            in response.json()["detail"]["message"]
        ):
            external_gameId = response.json()["detail"]["gameId"]
        else:
            external_gameId = response.json()["gameId"]
    except Exception as e:
        print(e)

        raise HTTPException(status_code=500, detail="Error creating game")
    if not external_gameId:
        raise HTTPException(
            status_code=500, detail="Error creating game. No gameId found"
        )

    create_task_body = []

    for task in taskList["taskList"]:

        development_value = task.get("development", 0)
        exploitation_value = task.get("exploitation", 0)
        management_value = task.get("management", 0)
        create_task_body.append(
            {
                "externalTaskId": str(task["id"]),
                "strategyId": "greengageStrategy",
                "params": [
                    {
                        "key": "variable_dimension_complexity",
                        "value": {
                            "development": development_value,
                            "exploitation": exploitation_value,
                            "management": management_value,
                        },
                    }
                ],
            }
        )

    tasks_created = None
    try:
        tasks_created = requests.post(
            f"http://{service_name}games/{external_gameId}/tasks/bulk",
            json={"tasks": create_task_body},
            headers={"X-API-Key": api_key},
        )

    except Exception as e:
        print("except Exception as e:")
        print(e)
        raise HTTPException(status_code=500, detail="Error creating tasks")

    if tasks_created.status_code == 200:
        coproductionprocess.game_id = external_gameId
        coproductionprocess.game_gamification_engine = "GAME"
        coproductionprocess.game_strategy = "behavioral"
        db.add(coproductionprocess)
        db.commit()
        db.refresh(coproductionprocess)
    response = tasks_created.json()
    response["gameId"] = external_gameId
    return response


# @router.put("/{process_id}")
# async def update_game(
#     *,
#     db: Session = Depends(deps.get_db),
#     current_user: Optional[models.User] = Depends(deps.get_current_active_user),
#     process_id: uuid.UUID,
#     task: dict,
# ) -> Any:
#     """
#     Update game by process_id.
#     """

#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")
#     if not crud.coproductionprocess.can_update(
#         user=current_user, object=coproductionprocess
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     task = task["task"]
#     game = await get_game(process_id=process_id)
#     taskList = game[0]["taskList"]
#     taskList.append(
#         {
#             "id": task["id"],
#             "management": task["management"],
#             "development": task["development"],
#             "exploitation": task["exploitation"],
#             "completed": False,
#             "subtaskList": [],
#             "players": [],
#         }
#     )

#     data = {
#         "active": True,
#         "id": coproductionprocess.game_id,
#         "name": "complexityGame",
#         "processId": str(coproductionprocess.id),
#         "filename": "game_1.json",
#         "tagList": ["process1", "process3"],
#         "taskList": taskList,
#     }

#     response = requests.put(
#         f"http://{serviceName}{PATH}",
#         json=data,
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     )

#     print("***********************************")
#     print('@router.put("/{process_id}")')
#     print("***********************************")
#     print(response.text)
#     print("-----------------------------------")
#     return response.text


# @router.delete("/{process_id}")
# async def delete_game(
#     *,
#     db: Session = Depends(deps.get_db),
#     current_user: Optional[models.User] = Depends(deps.get_current_active_user),
#     process_id: uuid.UUID,
# ) -> Any:
#     """
#     Delete game by process_id.
#     """
#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")
#     if not crud.coproductionprocess.can_update(
#         user=current_user, object=coproductionprocess
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     response = requests.delete(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}",
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     )

#     print("***********************************")
#     print('@router.delete("/{process_id}")')
#     print("***********************************")
#     print(response.text)
#     print("-----------------------------------")
#     return response.text


# @router.get("/{process_id}/leaderboard")
# async def get_leaderboard(
#     *,
#     db: Session = Depends(deps.get_db),
#     process_id: uuid.UUID,
#     # period="global",
# ) -> Any:
#     """
#     Get leaderboard by process_id.
#     """

#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")

#     response = requests.get(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/player/search",
#         params={
#             "period": "global",
#             "activityType": "development",
#         },
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     ).json()

#     return response


# @router.get("/{process_id}/{task_id}")
# async def get_task(
#     *,
#     db: Session = Depends(deps.get_db),
#     process_id: uuid.UUID,
#     task_id: uuid.UUID,
# ) -> Any:
#     """
#     Get task by process_id and task_id.
#     """
#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")

#     response = requests.get(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}",
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     ).json()

#     response = get_game_config(response, coproductionprocess)
#     return response


# @router.put("/{process_id}/{task_id}")
# async def update_task(
#     *,
#     db: Session = Depends(deps.get_db),
#     current_user: Optional[models.User] = Depends(deps.get_current_active_user),
#     process_id: uuid.UUID,
#     task_id: uuid.UUID,
#     data: dict,
# ) -> Any:
#     """
#     Update task by process_id and task_id.
#     data should be a dict with the following keys:
#     - development
#     - subtaskList (empty)
#     """
#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")
#     if not crud.coproductionprocess.can_update(
#         user=current_user, object=coproductionprocess
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     data["id"] = str(task_id)
#     data["subtaskList"] = []

#     response = requests.put(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task",
#         json=data,
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     )
#     print("***********************************")
#     print('@router.put("/{process_id}/{task_id}")')
#     print("***********************************")
#     print(response.json())
#     print("-----------------------------------")
#     return response.json()


# @router.put("/{process_id}/{task_id}/claim")
# async def add_claim(
#     *,
#     db: Session = Depends(deps.get_db),
#     current_user: Optional[models.User] = Depends(deps.get_current_active_user),
#     process_id: uuid.UUID,
#     task_id: uuid.UUID,
#     data: dict,
# ) -> Any:
#     """
#     Add claim to game by process_id and task_id.
#     data should contain:
#     - id
#     - name
#     - development
#     """

#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")
#     if not crud.coproductionprocess.can_update(
#         user=current_user, object=coproductionprocess
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")
#     if not await crud.user.get(db=db, id=data["id"]):
#         raise HTTPException(status_code=404, detail="User not found")

#     response = requests.put(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/claim",
#         json=data,
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     ).json()
#     response = get_game_config(response, coproductionprocess)
#     return response


# @router.put("/{process_id}/{task_id}/complete")
# async def complete_task(
#     *,
#     db: Session = Depends(deps.get_db),
#     current_user: Optional[models.User] = Depends(deps.get_current_active_user),
#     process_id: uuid.UUID,
#     task_id: uuid.UUID,
# ) -> Any:
#     """
#     Complete task by process_id and task_id.
#     """
#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")
#     if not crud.coproductionprocess.can_update(
#         user=current_user, object=coproductionprocess
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     response = requests.put(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/complete",
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     ).json()
#     response = get_game_config(response, coproductionprocess)
#     return response


# @router.delete("/{process_id}/{task_id}/revert")
# async def revert_task(
#     *,
#     db: Session = Depends(deps.get_db),
#     current_user: Optional[models.User] = Depends(deps.get_current_active_user),
#     process_id: uuid.UUID,
#     task_id: uuid.UUID,
# ) -> Any:
#     """
#     Complete task by process_id and task_id.
#     """
#     coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
#     if not coproductionprocess:
#         raise HTTPException(status_code=404, detail="CoproductionProcess not found")
#     if not coproductionprocess.game_id:
#         raise HTTPException(status_code=404, detail="Game not found")
#     if not crud.coproductionprocess.can_update(
#         user=current_user, object=coproductionprocess
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     # Revert claim
#     response = requests.put(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/revert",
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     )

#     # Get task
#     task = requests.get(
#         f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}",
#         headers={"Content-type": "application/json", "Accept": "*/*"},
#     )

#     # Delete players
#     for player in task.json()["players"]:
#         data = {
#             "development": 0,
#             "exploitation": 0,
#             "id": player["id"],
#             "management": 0,
#             "name": "string",
#         }
#         requests.delete(
#             f"http://{serviceName}{PATH}/{coproductionprocess.game_id}/task/{task_id}/removePlayer",
#             json=data,
#             headers={"Content-type": "application/json", "Accept": "*/*"},
#         )
#     print("***********************************")
#     print('@router.delete("/{process_id}/{task_id}/revert")')
#     print("***********************************")
#     print(response.json())
#     print("-----------------------------------")
#     print(task.json())
#     print("-----------------------------------")
#     return response.json()
