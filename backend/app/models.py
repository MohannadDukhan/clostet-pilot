from datetime import datetime
from typing import Optional, List
from .enums import Season, Gender, OutfitPart, Formality
from sqlmodel import SQLModel, Field, Relationship

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
    verified: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = Relationship(back_populates='items')
