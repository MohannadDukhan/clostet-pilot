from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from typing import List
from pathlib import Path
from .db import init_db, get_session
from .schemas import UserCreate, UserRead, ItemRead, ItemUpdate, ItemClassification  # ItemClassification was added earlier
from . import crud
from .config import settings
from .vision import classify_image
import os

app = FastAPI(title='Outfit Maker API', version='0.2.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# serve uploaded images
STORAGE_DIR = Path(__file__).resolve().parent.parent / 'storage'
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount('/storage', StaticFiles(directory=str(STORAGE_DIR)), name='storage')

@app.on_event('startup')
def on_startup():
    init_db()

# ---- Users ----
@app.get('/users', response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    return crud.list_users(session)

@app.post('/users', response_model=UserRead)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    return crud.create_user(session, payload.name, payload.gender, payload.city, payload.style_preferences)

# ---- Items ----
@app.post('/users/{user_id}/items', response_model=ItemRead)
async def upload_item(user_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, 'User not found')

    content = await file.read()
    item = crud.create_item_with_file(session, user_id, file.filename, content)

    print("auto_classify_on_upload =", settings.auto_classify_on_upload, "openai_key?", bool(settings.openai_api_key))


    # optional auto-classify
    if settings.auto_classify_on_upload:
        try:
            # resolve absolute path for the saved file
            abs_path = (STORAGE_DIR / item.image_url).resolve()
            pred = classify_image(str(abs_path))
            item = crud.update_item_classification(session, item.id, pred)
        except Exception as e:
            # don't fail the upload if classifier errors out
            print("auto-classify failed:", e)

    # return the (possibly) updated item
    return item

@app.get('/users/{user_id}/items', response_model=List[ItemRead])
def list_items(user_id: int, session: Session = Depends(get_session)):
    return crud.list_items_for_user(session, user_id)

@app.patch('/items/{item_id}', response_model=ItemRead)
def patch_item(item_id: int, payload: ItemUpdate, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(404, 'Item not found')
    return crud.update_item(session, item, **payload.dict(exclude_unset=True))

@app.delete('/items/{item_id}')
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(404, 'Item not found')
    crud.delete_item(session, item)
    return {'ok': True}

# ---- NEW: on-demand classification endpoint ----
@app.post('/items/{item_id}/classify', response_model=ItemRead)
def classify_item(item_id: int, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail='Item not found')
    if not item.image_url:
        raise HTTPException(status_code=400, detail='Item has no image')

    abs_path = (STORAGE_DIR / item.image_url).resolve()
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail='Image file missing')

    print("CLASSIFY → item:", item_id, "| path:", str(abs_path))
    try:
        pred = classify_image(str(abs_path))
        print("CLASSIFY ← prediction:", pred)
        updated = crud.update_item_classification(session, item_id, pred)
        return updated
    except Exception as e:
        import traceback
        print("CLASSIFY ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"classification failed: {e}")


@app.get("/debug/env")
def debug_env():
    from .config import settings
    return {
        "auto_classify_on_upload": settings.auto_classify_on_upload,
        "has_openai_key": bool(settings.openai_api_key),
    }

