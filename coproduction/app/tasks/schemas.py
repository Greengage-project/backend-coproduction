from enum import Enum
import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
from app.treeitems.schemas import *
from app.assets.schemas import *


class TaskCreate(TreeItemCreate):
    objective_id: Optional[uuid.UUID]
    problemprofiles: Optional[list]
    status: Optional[str]
    disabler_id: Optional[str]
    disabled_on: Optional[datetime]
    start_date: Optional[date]
    end_date: Optional[date]

    management: Optional[int]
    development: Optional[int]
    exploitation: Optional[int]


class TaskPatch(TreeItemPatch):
    problemprofiles: Optional[list]
    status: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]

    management: Optional[int]
    development: Optional[int]
    exploitation: Optional[int]


class Task(TreeItem, TaskCreate):
    class Config:
        orm_mode = True


class TaskOut(Task, TreeItemOut):
    phase_id: uuid.UUID


class TaskAssetContributionsOut(Task):
    assetsWithContribution: List[AssetOutContributions]

    class Config:
        orm_mode = True


class TaskReward(BaseModel):
    """
    Task reward schema for the API
    """

    minutes: int
    contribution: str
    contributionRating: float

    class Config:
        orm_mode = True
