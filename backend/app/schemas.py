from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .enums import Season, OutfitPart, Formality

class UserCreate(BaseModel):
    name: str
<<<<<<< HEAD
    city: str
    style_preferences: Optional[str] = None
=======
    gender: str
    city: str
    style_preferences: Optional[str] = None

>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027

class UserRead(BaseModel):
    id: int
    name: str
<<<<<<< HEAD
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
=======
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
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
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