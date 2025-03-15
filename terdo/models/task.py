from pydantic import BaseModel
from datetime import datetime


class Task(BaseModel):
    id: int
    name: str
    last_edited: datetime | None = None
