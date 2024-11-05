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


# check if game exists in gamification engine
@router.get("/{process_id}/exists")
async def game_exists(
    *,
    db: Session = Depends(deps.get_db),
    process_id: uuid.UUID,
) -> Any:
    """
    Check if game exists in gamification engine.
    """
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    response = requests.get(
        f"http://{service_name}games?page_size=all", headers={"X-API-Key": api_key}
    ).json()

    items = response.get("items", [])

    for game in items:
        if str(game["externalGameId"]) == str(process_id):
            return {
                "exists": True,
                "gameId": game["gameId"],
                "game_gamification_engine": "GAME",
                "game_strategy": "behavioral",
            }
    return {"exists": False}


@router.delete("/{game_id}")
async def delete_game(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
    game_id: str,
) -> Any:
    """
    Delete game by gameId in gamification engine.
    """
    response = requests.delete(
        f"http://{service_name}games/{game_id}",
        headers={"X-API-Key": api_key},
    )
    return response.json()


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


@router.get("/{process_id}/leaderboard")
async def get_leaderboard(
    *,
    db: Session = Depends(deps.get_db),
    process_id: uuid.UUID,
    # period="global",
) -> Any:
    """
    Get leaderboard by process_id
    """

    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        response = requests.get(
            f"http://{service_name}games/{coproductionprocess.game_id}/points",
            headers={"X-API-Key": api_key},
        ).json()

        array_externalTaskId = []
        array_externalUserId = []
        for task in response["task"]:
            array_externalTaskId.append(task["externalTaskId"])
            for point in task["points"]:
                if point["externalUserId"] not in array_externalUserId:
                    array_externalUserId.append(point["externalUserId"])

        try:
            all_task = crud.task.get_tasks(db=db, ids=array_externalTaskId)
            all_task_dict = {task["externalTaskId"]: task for task in all_task}

            for task in response["task"]:
                external_task = all_task_dict.get(task["externalTaskId"])
                if external_task:
                    task["name"] = external_task["name"]
                    task["status"] = external_task["status"]
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Error getting leaderboard.")

        users = await crud.user.get_users(db=db, ids=array_externalUserId)

        for task in response["task"]:
            for point in task["points"]:
                for user in users:
                    if user["id"] == point["externalUserId"]:
                        point["full_name"] = user["full_name"]
                        point["picture"] = user["picture"]
        response["game_gamification_engine"] = (
            coproductionprocess.game_gamification_engine
        )
        response["game_strategy"] = coproductionprocess.game_strategy
        return response
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error getting leaderboard")


# rewardPoints
"""
const res = await axiosInstance.post(
      `/${this.url}/rewardPoints/${taskId}/${userId}`,
      {
        points,
        contribution,
        contributionRating,
      }
    );
"""


@router.post("/{process_id}/rewardPoints/{task_id}/{user_id}")
async def reward_points(
    *,
    db: Session = Depends(deps.get_db),
    process_id: uuid.UUID,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    body: schemas.TaskReward,
) -> Any:
    """
    Reward points by process_id, task_id and user_id.
    """
    minutes = body.minutes
    contribution = body.contribution
    contributionRating = body.contributionRating
    coproductionprocess = await crud.coproductionprocess.get(db=db, id=process_id)
    if not coproductionprocess:
        raise HTTPException(status_code=404, detail="CoproductionProcess not found")
    if not coproductionprocess.game_id:
        raise HTTPException(status_code=404, detail="Game not found")
    #   'http://localhost:8000/api/v1/games/GAMEID/tasks/taskIdd/points' \
    game_id = coproductionprocess.game_id
    # check if contributionRating is number (float or int) and between 1 and 5
    if (
        not isinstance(contributionRating, (int, float))
        or contributionRating < 1
        or contributionRating > 5
    ):
        raise HTTPException(
            status_code=400,
            detail="contributionRating must be a number between 1 and 5",
        )

    if len(contribution) < 3:
        raise HTTPException(
            status_code=400,
            detail="contribution must have at least 3 characters",
        )
    response = requests.post(
        f"http://{service_name}games/{game_id}/tasks/{task_id}/points",
        json={
            "externalUserId": str(user_id),
            "data": {
                "minutes": minutes,
                "contribution": contribution,
                "contributionRating": contributionRating,
            },
        },
        headers={"X-API-Key": api_key},
    )

    return response.json()


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
