from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from .enums import Season, Gender, OutfitPart, Formality
from .models import Season, Formality, OutfitPart

class UserCreate(BaseModel):
    name: str
    gender: Gender
    city: str
    style_preferences: Optional[str] = None

class UserRead(BaseModel):
    id: int
    name: str
    gender: Gender
    city: str
    style_preferences: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ItemClassification(BaseModel):
    category: str
    color: str
    season: Season
    formality: Formality

    id: int
    user_id: int
    image_url: str
    original_filename: Optional[str] = None



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
    is_graphic: Optional[bool] = None
    target_gender: Optional[str] = None
    gender_source: Optional[str] = None
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
    target_gender: Optional[str] = None
    gender_source: Optional[str] = None
    notes: Optional[str] = None
    verified: Optional[bool] = None
