import os
from pathlib import Path
from typing import Iterable, Optional

from sqlmodel import Session, select

from .models import User, Item

# storage root: backend/storage
STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage"


# ---------- Users ----------

def create_user(session: Session, display_name: str) -> User:
    user = User(display_name=display_name)
    session.add(user)
    session.commit()
    session.refresh(user)

    # make per-user folder: storage/<user_id>/items
    (STORAGE_ROOT / str(user.id) / "items").mkdir(parents=True, exist_ok=True)
    return user


def list_users(session: Session) -> list[User]:
    return session.exec(select(User)).all()


def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


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


def create_item(session: Session, user_id: int, original_filename: str, stored_rel_path: str) -> Item:
    item = Item(
        user_id=user_id,
        original_filename=original_filename,
        stored_path=stored_rel_path,
        source="manual",    # later can be "llm" when we auto-fill fields
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_items(session: Session, user_id: int) -> list[Item]:
    stmt = select(Item).where(Item.user_id == user_id).order_by(Item.uploaded_at.desc())
    return session.exec(stmt).all()


def get_item(session: Session, item_id: int) -> Optional[Item]:
    return session.get(Item, item_id)


def update_item(session: Session, item: Item, **fields) -> Item:
    # only set keys that were provided (not None)
    for k, v in fields.items():
        if v is not None:
            setattr(item, k, v)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_item(session: Session, item: Item) -> None:
    # try deleting the file on disk
    file_path = STORAGE_ROOT / item.stored_path
    try:
        file_path.unlink(missing_ok=True)
    except Exception:
        pass

    session.delete(item)
    session.commit()
