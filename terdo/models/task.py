from pydantic import BaseModel
from datetime import datetime


class Task(BaseModel):
    name: str
    last_edited: datetime
