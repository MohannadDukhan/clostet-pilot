import uuid
from pathlib import Path
from typing import Iterable, Optional, List

from sqlmodel import Session, select

from .models import User, Item, Outfit, Feedback

# storage root: backend/storage
STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage"


def create_user(
    session: Session,
    name: str,
    city: str,
    style_preferences: Optional[str],
) -> User:
    # normalize empty style_preferences to None
    if style_preferences is not None and style_preferences.strip() == "":
        style_preferences = None

    user = User(name=name, city=city, style_preferences=style_preferences)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_users(session: Session) -> Iterable[User]:
    return session.exec(select(User).order_by(User.id)).all()


def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

def update_user(
    session: Session,
    user: User,
    *,
    name: Optional[str] = None,
    city: Optional[str] = None,
    style_preferences: Optional[str] = None,
) -> User:
    """Update basic fields on an existing user and persist them."""
    if name is not None:
        user.name = name
    if city is not None:
        user.city = city

    if style_preferences is not None:
        style_preferences = style_preferences.strip()
        user.style_preferences = style_preferences or None

    session.add(user)
    session.commit()
    session.refresh(user)
    return user



def create_item_with_file(
    session: Session,
    user_id: int,
    filename: str,
    content: bytes,
    content_hash: str,
) -> Item:
    user_dir = STORAGE_ROOT / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    ext = (Path(filename).suffix or ".jpg").lower()
    rel = Path(str(user_id)) / f"{uuid.uuid4().hex}{ext}"
    abs_path = STORAGE_ROOT / rel
    abs_path.write_bytes(content)

    item = Item(
        user_id=user_id,
        image_url=str(rel).replace("\\", "/"),
        original_filename=filename,
        content_hash=content_hash,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def find_item_by_hash(
    session: Session,
    user_id: int,
    content_hash: str,
):
  stmt = (
      select(Item)
      .where(Item.user_id == user_id, Item.content_hash == content_hash)
      .limit(1)
  )
  return session.exec(stmt).first()


def list_items_for_user(session: Session, user_id: int) -> List[Item]:
    stmt = (
        select(Item)
        .where(Item.user_id == user_id)
        .order_by(Item.id.desc())
    )
    return session.exec(stmt).all()


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
    file_path = STORAGE_ROOT / item.image_url
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass

    session.delete(item)
    session.commit()


# --- helper for classification updates ---
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


# ---------- User helpers ----------

def update_user(session: Session, user: User, **kwargs) -> User:
    """Partial update for a user (e.g. change name/city/style)."""
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user: User) -> None:
    """Cascade delete a user: feedback -> outfits -> items -> user."""
    # delete all feedback rows for this user
    feedbacks = session.exec(select(Feedback).where(Feedback.user_id == user.id)).all()
    for fb in feedbacks:
        session.delete(fb)

    # delete all outfits for this user
    outfits = session.exec(select(Outfit).where(Outfit.user_id == user.id)).all()
    for outfit in outfits:
        delete_outfit(session, outfit)

    # delete all items (and their files) for this user
    items = session.exec(select(Item).where(Item.user_id == user.id)).all()
    for item in items:
        delete_item(session, item)

    session.delete(user)
    session.commit()


# ---------- Optional: explicit file + item creation helpers ----------

def save_item_file(user_id: int, file_bytes: bytes, original_filename: str) -> str:
    """Save raw bytes under storage/<user_id>/items/, return path relative to STORAGE_ROOT."""
    user_dir = STORAGE_ROOT / str(user_id) / "items"
    user_dir.mkdir(parents=True, exist_ok=True)

    base = Path(original_filename).name
    target = user_dir / base

    i = 1
    while target.exists():
        stem = target.stem
        ext = target.suffix
        target = user_dir / f"{stem}_{i}{ext}"
        i += 1

    target.write_bytes(file_bytes)
    return str(target.relative_to(STORAGE_ROOT))


def create_item(
    session: Session,
    user_id: int,
    original_filename: str,
    image_url: str,
) -> Item:
    """Create an Item row, used together with save_item_file()."""
    item = Item(
        user_id=user_id,
        original_filename=original_filename,
        image_url=image_url,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


# ---------- Outfit CRUD ----------

def create_outfit(
    session: Session,
    user_id: int,
    top_item_id: Optional[int] = None,
    bottom_item_id: Optional[int] = None,
    shoes_item_id: Optional[int] = None,
    accessory_item_id: Optional[int] = None,
    outerwear_item_id: Optional[int] = None,
    onepiece_item_id: Optional[int] = None,
    score: Optional[float] = None,
) -> Outfit:
    outfit = Outfit(
        user_id=user_id,
        top_item_id=top_item_id,
        bottom_item_id=bottom_item_id,
        shoes_item_id=shoes_item_id,
        accessory_item_id=accessory_item_id,
        outerwear_item_id=outerwear_item_id,
        onepiece_item_id=onepiece_item_id,
        score=score,
    )
    session.add(outfit)
    session.commit()
    session.refresh(outfit)
    return outfit


def get_outfit(session: Session, outfit_id: int) -> Optional[Outfit]:
    return session.get(Outfit, outfit_id)


def list_outfits(session: Session, user_id: int) -> List[Outfit]:
    stmt = select(Outfit).where(Outfit.user_id == user_id)
    return session.exec(stmt).all()


def update_outfit(session: Session, outfit: Outfit, **fields) -> Outfit:
    for k, v in fields.items():
        if v is not None:
            setattr(outfit, k, v)
    session.add(outfit)
    session.commit()
    session.refresh(outfit)
    return outfit


def delete_outfit(session: Session, outfit: Outfit) -> None:
    session.delete(outfit)
    session.commit()


# ---------- Feedback CRUD ----------

def create_feedback(
    session: Session,
    user_id: int,
    outfit_id: int,
    score: Optional[float] = None,
) -> Feedback:
    feedback = Feedback(
        user_id=user_id,
        outfit_id=outfit_id,
        score=score,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def get_feedback(session: Session, feedback_id: int) -> Optional[Feedback]:
    return session.get(Feedback, feedback_id)


def list_feedback(
    session: Session,
    user_id: Optional[int] = None,
    outfit_id: Optional[int] = None,
) -> List[Feedback]:
    stmt = select(Feedback)
    if user_id is not None:
        stmt = stmt.where(Feedback.user_id == user_id)
    if outfit_id is not None:
        stmt = stmt.where(Feedback.outfit_id == outfit_id)
    return session.exec(stmt).all()


def update_feedback(session: Session, feedback: Feedback, **fields) -> Feedback:
    for k, v in fields.items():
        if v is not None:
            setattr(feedback, k, v)
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def delete_feedback(session: Session, feedback: Feedback) -> None:
    session.delete(feedback)
    session.commit()
