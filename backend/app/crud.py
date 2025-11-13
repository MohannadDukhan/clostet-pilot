import uuid
from pathlib import Path
from typing import Iterable, Optional, List
from sqlmodel import Session, select
<<<<<<< HEAD
from .models import User, Item
=======

from .models import User, Item, Outfit
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027

# storage root: backend/storage
STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage"

def create_user(session: Session, name: str, city: str, style_preferences: Optional[str]) -> User:
    # normalize empty style_preferences to None
    if style_preferences is not None and style_preferences.strip() == "":
        style_preferences = None

<<<<<<< HEAD
    user = User(name=name, city=city, style_preferences=style_preferences)
=======
# ---------- Users ----------

def create_user(session: Session, name: str, gender: str, city: str, style_preferences=None ) -> User:
    user = User(name=name, gender=gender, city=city, style_preferences=style_preferences)
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_users(session: Session) -> Iterable[User]:
    return session.exec(select(User).order_by(User.id)).all()

def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

<<<<<<< HEAD
def create_item_with_file(session: Session, user_id: int, filename: str, content: bytes) -> Item:
    user_dir = STORAGE_ROOT / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    ext = (Path(filename).suffix or ".jpg").lower()
    rel = Path(str(user_id)) / f"{uuid.uuid4().hex}{ext}"
    abs_path = STORAGE_ROOT / rel
    abs_path.write_bytes(content)
    item = Item(user_id=user_id, image_url=str(rel).replace("\\","/"), original_filename=filename)
=======
def update_user(session, user, **kwargs):
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def delete_user(session, user):
    feedbacks = session.exec(select(Feedback).where(Feedback.user_id == user.id)).all()
    for fb in feedbacks:
        session.delete(fb)
    # Delete all outfits for this user (and their feedback)
    outfits = session.exec(select(Outfit).where(Outfit.user_id == user.id)).all()
    for outfit in outfits:
        delete_outfit(session, outfit)
    # Delete all items for this user (and their files)
    items = session.exec(select(Item).where(Item.user_id == user.id)).all()
    for item in items:
        delete_item(session, item)
    session.delete(user)
    session.commit()


# ---------- Items / Files ----------

def save_item_file(user_id: int, file_bytes: bytes, original_filename: str) -> str:
    """
    Saves the uploaded bytes under storage/<user_id>/items/<filename>.
    Ensures uniqueness if the name already exists.
    Returns the path *relative to* storage/ (e.g. "1/items/myshirt_1.jpg").
    """
    user_dir = STORAGE_ROOT / str(user_id) / "items"
    user_dir.mkdir(parents=True, exist_ok=True)

    # sanitize: keep only the name part
    base = Path(original_filename).name
    target = user_dir / base

    i = 1
    while target.exists():
        stem, ext = os.path.splitext(base)
        target = user_dir / f"{stem}_{i}{ext}"
        i += 1

    with open(target, "wb") as f:
        f.write(file_bytes)

    # return path relative to storage/
    return str(target.relative_to(STORAGE_ROOT))


def create_item(session: Session, user_id: int, original_filename: str, image_url: str) -> Item:
    item = Item(
        user_id=user_id,
        original_filename=original_filename,
        image_url=image_url,
        source="manual",    # later can be "llm" when we auto-fill fields
    )
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

<<<<<<< HEAD
def list_items_for_user(session: Session, user_id: int) -> List[Item]:
    return session.exec(select(Item).where(Item.user_id==user_id).order_by(Item.id.desc())).all()
=======

def list_items(session: Session, user_id: int) -> list[Item]:
    stmt = select(Item).where(Item.user_id == user_id).order_by(Item.created_at.desc())
    return session.exec(stmt).all()

>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027

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

    if data.get("outfit_part"):
        item.outfit_part = data["outfit_part"]

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

<<<<<<< HEAD
=======

def delete_item(session: Session, item: Item) -> None:
    # try deleting the file on disk
    file_path = STORAGE_ROOT / item.image_url
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass

    session.delete(item)
    session.commit()


# ---------- Outfits ----------

def create_outfit(session, user_id, top_item_id=None, bottom_item_id=None, shoes_item_id=None, accessory_item_id=None, outerwear_item_id=None, onepiece_item_id=None, score=None):
    outfit = Outfit(
        user_id=user_id,
        top_item_id=top_item_id,
        bottom_item_id=bottom_item_id,
        shoes_item_id=shoes_item_id,
        accessory_item_id=accessory_item_id,
        outerwear_item_id=outerwear_item_id,
        onepiece_item_id=onepiece_item_id,
        score=score
    )
    session.add(outfit)
    session.commit()
    session.refresh(outfit)
    return outfit

def get_outfit(session, outfit_id):
    return session.get(Outfit, outfit_id)

def list_outfits(session, user_id):
    return session.exec(select(Outfit).where(Outfit.user_id == user_id)).all()

def update_outfit(session, outfit, **fields):
    for k, v in fields.items():
        if v is not None:
            setattr(outfit, k, v)
    session.add(outfit)
    session.commit()
    session.refresh(outfit)
    return outfit

def delete_outfit(session, outfit):
    session.delete(outfit)
    session.commit()

# ---------- Feedback ----------
from .models import Feedback

def create_feedback(session, user_id, outfit_id, score=None):
    feedback = Feedback(
        user_id=user_id,
        outfit_id=outfit_id,
        score=score
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback

def get_feedback(session, feedback_id):
    return session.get(Feedback, feedback_id)

def list_feedback(session, user_id=None, outfit_id=None):
    stmt = select(Feedback)
    if user_id is not None:
        stmt = stmt.where(Feedback.user_id == user_id)
    if outfit_id is not None:
        stmt = stmt.where(Feedback.outfit_id == outfit_id)
    return session.exec(stmt).all()

def update_feedback(session, feedback, **fields):
    for k, v in fields.items():
        if v is not None:
            setattr(feedback, k, v)
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback

def delete_feedback(session, feedback):
    session.delete(feedback)
    session.commit()
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
