import uuid
from pathlib import Path
from typing import Iterable, Optional, List
from sqlmodel import Session, select
from .models import User, Item

# storage root: backend/storage
STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage"

def create_user(session: Session, name: str, gender: Optional[str], city: Optional[str], style_preferences: Optional[str]) -> User:
    user = User(name=name, gender=gender, city=city, style_preferences=style_preferences)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def list_users(session: Session) -> Iterable[User]:
    return session.exec(select(User).order_by(User.id)).all()

def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

def create_item_with_file(session: Session, user_id: int, filename: str, content: bytes) -> Item:
    user_dir = STORAGE_ROOT / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    ext = (Path(filename).suffix or ".jpg").lower()
    rel = Path(str(user_id)) / f"{uuid.uuid4().hex}{ext}"
    abs_path = STORAGE_ROOT / rel
    abs_path.write_bytes(content)
    item = Item(user_id=user_id, image_url=str(rel).replace("\\","/"), original_filename=filename)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def list_items_for_user(session: Session, user_id: int) -> List[Item]:
    return session.exec(select(Item).where(Item.user_id==user_id).order_by(Item.id.desc())).all()

def get_item(session: Session, item_id: int) -> Optional[Item]:
    return session.get(Item, item_id)

def update_item(session: Session, item: Item, **fields) -> Item:
    for k, v in fields.items():
        if v is not None:
            setattr(item, k, v)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def delete_item(session: Session, item: Item) -> None:
    file_path = (STORAGE_ROOT / item.image_url)
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass
    session.delete(item)
    session.commit()

# --- new helper for classification updates ---
def update_item_classification(session: Session, item_id: int, data: dict) -> Item:
    """Map vision output to DB columns + normalize enums."""
    item = session.get(Item, item_id)
    if not item:
        raise ValueError("item not found")

    # direct
    if data.get("category"):
        item.category = data["category"]

    # color → primary_color
    if data.get("color"):
        item.primary_color = data["color"]

    # normalize season/formality to snake_case used in models
    if data.get("season"):
        s = data["season"].strip().lower()
        s = s.replace("-", "_").replace(" ", "_")  # all-season → all_season
        item.season = s

    if data.get("formality"):
        f = data["formality"].strip().lower()
        f = f.replace("-", "_").replace(" ", "_")  # business casual → business_casual
        item.formality = f

    session.add(item)
    session.commit()
    session.refresh(item)
    return item

