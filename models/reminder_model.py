from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReminderModel(BaseModel):
    id: int
    user_id: int | str
    chat_id: int | str
    message: str
    time: str | datetime # Accepting both for now as DB might return string
