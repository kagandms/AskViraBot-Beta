from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NoteModel(BaseModel):
    id: int
    user_id: int | str
    content: str
    created_at: Optional[datetime] = None
