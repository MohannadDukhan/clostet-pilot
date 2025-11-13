from datetime import datetime
from typing import Optional, List
from .enums import Season, OutfitPart, Formality
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from sqlalchemy import Column
from sqlalchemy.types import Enum as SqlEnum

<<<<<<< HEAD
=======
#Enums
class Reaction(str, Enum):
    LIKE="like"; DISLIKE="dislike"

class Formality(str, Enum):
    CASUAL = "casual"
    SMART_CASUAL = "smart_casual"
    SEMI_FORMAL = "semi_formal"
    FORMAL = "formal"
    BUSINESS_CASUAL = "business_casual"
    SPORTY = "sporty"

class OutfitPart(str, Enum):
    TOPS = "tops"
    BOTTOMS = "bottoms"
    OUTERWEAR = "outerwear"
    DRESSES = "dresses"
    SHOES = "shoes"
    ACCESSORIES = "accessories"
    ONEPIECE= "onepiece"

class Category(str, Enum):
    # Top categories
    T_SHIRT = "t_shirt"
    SHIRT = "shirt"
    POLO = "polo"
    SWEATER = "sweater"
    TANK_TOP = "tank top"
    HOODIE = "hoodie"
    DRESS = "dress"
    CROP_TOP = "crop top"
    # Bottom categories
    LEGGINGS = "leggings"
    SHORTS = "shorts"
    SKIRT = "skirt"
    PANTS = "pants"
    JEANS = "jeans"
    CHINOS = "chinos"
    # Outerwear categories
    JACKET = "jacket"
    COAT = "coat"
    BLAZER = "blazer"
    CARDIGAN = "cardigan"
    LEATHER_JACKET = "leather_jacket"
    PUFFER_JACKET = "puffer_jacket"
    #Shoes categories
    SNEAKERS = "sneakers"
    BOOTS = "boots"
    SANDALS = "sandals"
    DRESS_SHOES = "dress_shoes"
    HEELS = "heels"
    FLATS = "flats"
    LOAFERS = "loafers"
    #Accessories categories
    HAT = "hat"
    SCARF = "scarf"
    BELT = "belt"
    BAG = "bag"
    JEWELRY = "jewelry"
    WATCH = "watch"

class TargetGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"

>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
class User(SQLModel, table=True):
    # fields in the table
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
<<<<<<< HEAD
    city: str
    style_preferences: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    items: List['Item'] = Relationship(back_populates='user')
=======
    gender: str # can be male, female, other
    city: str
    style_preferences: Optional[str] = None # {"pref_color":["blue","black"], "pref_formality":"casual"}
    feedback_user: float = 0.0 #average score for user, help not repeat prev outfits if disliked
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # one user has many items
    items: list["Item"] = Relationship(back_populates="user") # can access all items of user, not row in table
    outfits: list["Outfit"] = Relationship(back_populates="user") # can get user outfits
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027

class Item(SQLModel, table=True):
    
    #fields in the table
    id: Optional[int] = Field(default=None, primary_key=True)
<<<<<<< HEAD
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
    notes: Optional[str] = None
    verified: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = Relationship(back_populates='items')
=======
    user_id: int = Field(foreign_key="user.id")
    
    #fields filled by LLM or user
    outfit_part: Optional[OutfitPart] = Field(default=None, index=True, nullable=True)
    category: Optional[Category] = Field(default=None, index=True, nullable=True)
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    formality: Optional[Formality] = Field(default=None, index=True)
    season: Optional[str] = None # summer, winter, fall, spring, all-season
    is_graphic: Optional[bool] = None
    target_gender: TargetGender = Field(default=TargetGender.UNISEX, index=True)
    gender_source: Optional[str] = None
    gender_confidence: Optional[float] = None
    verified: bool = Field(default=False) # whether user has verified the LLM's description
    source: Optional[str] = None # "llm" or "manual"
    
    #fields for file storage
    original_filename: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relationship to the user
    user: Optional[User] = Relationship(back_populates="items")

class Outfit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    top_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    bottom_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    shoes_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    accessory_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    outerwear_item_id: Optional[int] = Field(default=None, foreign_key="item.id", index=True)
    onepiece_item_id: Optional[int] = Field(default=None, foreign_key="item.id", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    score: Optional[float] = Field(default=None, index=True)

    user: Optional[User] = Relationship(back_populates="outfits")

class Feedback(SQLModel, table=True):
    id:Optional[int] = Field(default=None, primary_key=True)
    outfit_id: int = Field(foreign_key="outfit.id")
    user_id: int = Field(foreign_key="user.id")
    score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship()
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
