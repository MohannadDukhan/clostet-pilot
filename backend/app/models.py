from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from .enums import Season, OutfitPart, Formality


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: str
    style_preferences: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    items: List["Item"] = Relationship(back_populates="user")
    outfits: List["Outfit"] = Relationship(back_populates="user")


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    content_hash: Optional[str] = Field(default=None, index=True)

    # file info
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
    notes: Optional[str] = None
    verified: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    user: Optional["User"] = Relationship(back_populates="items")


class Outfit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    top_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    bottom_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    shoes_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    accessory_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    outerwear_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    onepiece_item_id: Optional[int] = Field(default=None, foreign_key="item.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    score: Optional[float] = Field(default=None)

    # relationships
    user: Optional["User"] = Relationship(back_populates="outfits")


class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    outfit_id: int = Field(foreign_key="outfit.id")
    user_id: int = Field(foreign_key="user.id")
    score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional["User"] = Relationship()
