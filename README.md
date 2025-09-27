# closet pilot

a tiny wardrobe app: upload clothing images, see them in your wardrobe, edit basic fields (category/color/season/formality/notes). later, we’ll plug in:
- **model A (LLM)** to classify the item’s fields
- **model B (LLM)** to generate outfits from your wardrobe + a request (e.g., “semi-formal dinner”)

---

## stack

- **backend:** FastAPI + SQLModel (SQLite), serves images from `backend/storage`
- **frontend:** React (Vite) + Axios

> note: `backend/storage/`, the SQLite DB (`*.sqlite`), and virtualenv are in `.gitignore`.

---

## run it locally

1) backend (FastAPI)

cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload

API docs: http://127.0.0.1:8000/docs
images served under: http://127.0.0.1:8000/images/<stored_path>

2) frontend (Vite)

cd frontend
npm install
npm run dev
open the printed URL (usually http://localhost:5173)

3) quick flow

create user (top bar)
upload item (choose image → upload)
wardrobe shows your item; click edit, fill fields, save (collapses to summary)

project goals (next)

plug in LLM to auto-fill item fields (category/color/season/formality)
add “make outfit” flow (LLM proposes outfit using wardrobe + request)
basic auth later if we need it
