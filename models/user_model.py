
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserModel(BaseModel):
    user_id: int | str
    language: str = "en"
    coins: int = 0
    created_at: Optional[datetime] = None
    
    # Optional: Methods for business logic if needed, 
    # but initially just data structure.
