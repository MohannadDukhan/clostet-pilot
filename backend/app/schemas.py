from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .enums import Season, OutfitPart, Formality

class UserCreate(BaseModel):
    name: str
    city: str
    style_preferences: Optional[str] = None

class UserRead(BaseModel):
    id: int
    name: str
    city: str
    style_preferences: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class ItemRead(BaseModel):
    id: int
    user_id: int
    image_url: str
    original_filename: Optional[str] = None
    outfit_part: Optional[OutfitPart] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[Formality] = None
    season: Optional[Season] = None
    notes: Optional[str] = None
    verified: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ItemUpdate(BaseModel):
    outfit_part: Optional[OutfitPart] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[Formality] = None
    season: Optional[Season] = None
    is_graphic: Optional[bool] = None
    notes: Optional[str] = None
    verified: Optional[bool] = None
