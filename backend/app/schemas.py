from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .enums import Season, OutfitPart, Formality


# ---------- Users ----------

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


class UserUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    style_preferences: Optional[str] = None


# ---------- Items ----------

class ItemCreate(BaseModel):
    user_id: int
    image_url: Optional[str] = None
    original_filename: Optional[str] = None
    outfit_part: Optional[OutfitPart] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    primary_color_hex: Optional[str] = None
    primary_color_hsv: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[Formality] = None
    season: Optional[Season] = None
    is_graphic: Optional[bool] = None
    notes: Optional[str] = None
    verified: Optional[bool] = None


class ItemRead(BaseModel):
    id: int
    user_id: int
    image_url: str
    original_filename: Optional[str] = None
    outfit_part: Optional[OutfitPart] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    primary_color_hex: Optional[str] = None
    primary_color_hsv: Optional[str] = None
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
    primary_color_hex: Optional[str] = None
    primary_color_hsv: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[Formality] = None
    season: Optional[Season] = None
    is_graphic: Optional[bool] = None
    notes: Optional[str] = None
    verified: Optional[bool] = None


# ---------- Outfits ----------

class OutfitCreate(BaseModel):
    user_id: int
    top_item_id: Optional[int] = None
    bottom_item_id: Optional[int] = None
    shoes_item_id: Optional[int] = None
    accessory_item_id: Optional[int] = None
    outerwear_item_id: Optional[int] = None
    onepiece_item_id: Optional[int] = None
    score: Optional[float] = None


class OutfitRead(BaseModel):
    id: int
    user_id: int
    top_item_id: Optional[int] = None
    bottom_item_id: Optional[int] = None
    shoes_item_id: Optional[int] = None
    accessory_item_id: Optional[int] = None
    outerwear_item_id: Optional[int] = None
    onepiece_item_id: Optional[int] = None
    score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OutfitUpdate(BaseModel):
    top_item_id: Optional[int] = None
    bottom_item_id: Optional[int] = None
    shoes_item_id: Optional[int] = None
    accessory_item_id: Optional[int] = None
    outerwear_item_id: Optional[int] = None
    onepiece_item_id: Optional[int] = None
    score: Optional[float] = None


# ---------- Feedback ----------

class FeedbackCreate(BaseModel):
    user_id: int
    outfit_id: int
    score: Optional[float] = None


class FeedbackRead(BaseModel):
    id: int
    user_id: int
    outfit_id: int
    score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackUpdate(BaseModel):
    score: Optional[float] = None
