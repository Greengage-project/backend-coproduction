import uuid
from datetime import datetime
from typing import List, Optional
from app.general.utils.AllOptional import AllOptional
from pydantic import BaseModel, validator, root_validator
import requests
from app.config import settings

class RatingBase(BaseModel):
    value: int
    artefact_id: uuid.UUID
    artefact_type: str
    title: Optional[str]
    text: str

    @validator('value')
    def value_not_greater_than_5(cls, v):
        if v > 5 or v < 0:
            raise ValueError('must be between 0 and 5')
        return v

class RatingCreate(RatingBase):
    pass


class RatingPatch(RatingCreate, metaclass=AllOptional):
    pass


class Rating(RatingBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]

    user_id: str

    class Config:
        orm_mode = True


class RatingOut(Rating):
    pass
"""     user: Optional[dict]

    @root_validator(pre=True)
    def get_user_data_from_auth_microservice(cls, values):
        id = values["user_id"]
        try:
            newValues = {**values}
            response = requests.get(f"http://{settings.AUTH_SERVICE}/auth/api/v1/users/{id}", headers={
                "X-API-Key": "secret"
            }).json()
            newValues["user"] = response
            return newValues
        except:
            return values """