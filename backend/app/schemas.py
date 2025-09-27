from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ---------- Users ----------

class UserCreate(BaseModel):
    display_name: str


class UserRead(BaseModel):
    id: int
    display_name: str

    class Config:
        from_attributes = True   # allow reading from SQLModel objects


# ---------- Items ----------

class ItemRead(BaseModel):
    id: int
    user_id: int
    original_filename: str
    stored_path: str
    uploaded_at: datetime

    category: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    formality: Optional[str] = None
    notes: Optional[str] = None
    verified: bool
    source: Optional[str] = None

    class Config:
        from_attributes = True


class ItemUpdate(BaseModel):
    # everything optional because it's a PATCH
    category: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    formality: Optional[str] = None
    notes: Optional[str] = None
    verified: Optional[bool] = None
