from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ---------- Users ----------

class UserCreate(BaseModel):
    name: str
    gender: str
    city: str
    style_preferences: Optional[str] = None


class UserRead(BaseModel):
    id: int
    name: str
    gender: str
    city: str
    style_preferences: Optional[str] = None
    feedback_user: float
    created_at: datetime
    class Config:
        from_attributes = True   # allow reading from SQLModel objects

class UserUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    style_preferences: Optional[str] = None

# ---------- Items ----------

class ItemCreate(BaseModel):
    user_id: int
    original_filename: Optional[str] = None
    image_url: Optional[str] = None
    outfit_part: Optional[str] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[str] = None
    season: Optional[str] = None
    is_graphic: Optional[bool] = None
    target_gender: Optional[str] = None
    gender_source: Optional[str] = None
    gender_confidence: Optional[float] = None
    verified: Optional[bool] = None
    source: Optional[str] = None

class ItemRead(BaseModel):
    id: int
    user_id: int
    original_filename: Optional[str] = None
    image_url: Optional[str] = None
    outfit_part: Optional[str] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[str] = None
    season: Optional[str] = None
    is_graphic: Optional[bool] = None
    target_gender: Optional[str] = None
    gender_source: Optional[str] = None
    gender_confidence: Optional[float] = None
    verified: Optional[bool] = None
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ItemUpdate(BaseModel):
    original_filename: Optional[str] = None
    image_url: Optional[str] = None
    outfit_part: Optional[str] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[str] = None
    season: Optional[str] = None
    is_graphic: Optional[bool] = None
    target_gender: Optional[str] = None
    gender_source: Optional[str] = None
    gender_confidence: Optional[float] = None
    verified: Optional[bool] = None
    source: Optional[str] = None

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