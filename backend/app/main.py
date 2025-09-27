from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from typing import List

from .db import init_db, get_session
from .schemas import UserCreate, UserRead, ItemRead, ItemUpdate
from . import crud

app = FastAPI(title="Closet Pilot API", version="0.1.0")

# allow the Vite dev server to call our API during local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# serve files under backend/storage/ at /images/*
app.mount(
    "/images",
    StaticFiles(directory=str(crud.STORAGE_ROOT), html=False),
    name="images",
)

# ---------- Users ----------
@app.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    return crud.create_user(session, payload.display_name)

@app.get("/users", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    return crud.list_users(session)

# ---------- Items ----------
@app.post("/users/{user_id}/items", response_model=ItemRead)
async def upload_item(user_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    content = await file.read()
    rel_path = crud.save_item_file(user_id, content, file.filename)
    return crud.create_item(session, user_id, file.filename, rel_path)

@app.get("/users/{user_id}/items", response_model=List[ItemRead])
def list_user_items(user_id: int, session: Session = Depends(get_session)):
    if not crud.get_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return crud.list_items(session, user_id)

@app.patch("/items/{item_id}", response_model=ItemRead)
def patch_item(item_id: int, payload: ItemUpdate, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.update_item(session, item, **payload.model_dump(exclude_none=True))

@app.delete("/items/{item_id}")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    crud.delete_item(session, item)
    return {"ok": True}
