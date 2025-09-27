from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    display_name: str

    # back-reference: one user has many items
    items: list["Item"] = Relationship(back_populates="user")


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # who owns this item
    user_id: int = Field(foreign_key="user.id")

    # file info
    original_filename: str
    stored_path: str                    # path under backend/storage/
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # text fields that the future LLM can fill, user can edit
    category: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    formality: Optional[str] = None
    notes: Optional[str] = None
    verified: bool = Field(default=False)

    source: Optional[str] = None        # "llm" or "manual"

    # relationship to the user
    user: Optional[User] = Relationship(back_populates="items")
