from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

class Formality(str, Enum):
    CASUAL = "casual"
    BUSINESS_CASUAL = "business_casual"
    SEMI_FORMAL = "semi_formal"
    FORMAL = "formal"

class Season(str, Enum):
    SUMMER = "summer"
    WINTER = "winter"
    ALL_SEASON = "all_season"
    SPRING = "spring"
    FALL = "fall"


# Gender enum for strict validation
class Gender(str, Enum):
    male = "male"
    female = "female"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gender: Gender
    city: str
    style_preferences: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    items: List['Item'] = Relationship(back_populates='user')

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    image_url: str  # relative path under /storage
    original_filename: Optional[str] = None

    # predicted/edited attributes
    outfit_part: Optional[str] = None
    category: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[str] = None
    season: Optional[str] = None
    is_graphic: Optional[bool] = None
    target_gender: Optional[str] = None
    gender_source: Optional[str] = None
    notes: Optional[str] = None
    verified: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = Relationship(back_populates='items')
