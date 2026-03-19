from datetime import datetime, date
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from .enums import Season, OutfitPart, Formality


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = Field(default=None)
    hashed_password: Optional[str] = Field(default=None)
    city: str
    style_preferences: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relationships
    items: List["Item"] = Relationship(back_populates="user")
    outfits: List["Outfit"] = Relationship(back_populates="user")
    outfit_history: List["OutfitHistory"] = Relationship(back_populates="user")


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
    primary_color_hex: Optional[str] = None  # #rrggbb format
    primary_color_hsv: Optional[str] = None  # "hue,saturation,value" format
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


class LikedOutfit(SQLModel, table=True):
    """Tracks colour combinations the user has liked/worn — used to avoid repetition."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    color_fingerprint: str  # e.g. "black,blue,white"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DislikedOutfit(SQLModel, table=True):
    """Tracks colour combinations the user has disliked — penalised in future suggestions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    color_fingerprint: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OutfitHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    requested_date: Optional[date] = None
    city: Optional[str] = None
    weather_temp_c: Optional[float] = None
    weather_condition: Optional[str] = None
    inferred_season: Optional[str] = None
    requested_formality: Optional[str] = None

    top_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    bottom_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    outerwear_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    shoes_item_id: Optional[int] = Field(default=None, foreign_key="item.id")

    top_category: Optional[str] = None
    top_color: Optional[str] = None
    top_season: Optional[str] = None
    top_formality: Optional[str] = None

    bottom_category: Optional[str] = None
    bottom_color: Optional[str] = None
    bottom_season: Optional[str] = None
    bottom_formality: Optional[str] = None

    outerwear_category: Optional[str] = None
    outerwear_color: Optional[str] = None
    outerwear_season: Optional[str] = None
    outerwear_formality: Optional[str] = None

    shoes_category: Optional[str] = None
    shoes_color: Optional[str] = None
    shoes_season: Optional[str] = None
    shoes_formality: Optional[str] = None

    user: Optional["User"] = Relationship(back_populates="outfit_history")
