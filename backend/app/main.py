import random
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
<<<<<<< HEAD
from typing import List, Optional
from pathlib import Path
=======
from typing import List
from datetime import date
import requests
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027

from .db import init_db, get_session
from .schemas import UserCreate, UserRead, ItemRead, ItemUpdate, UserUpdate, OutfitCreate, OutfitRead, OutfitUpdate, FeedbackCreate, FeedbackRead, FeedbackUpdate
from . import crud
from .config import settings
from .vision import classify_image

app = FastAPI(title="Outfit Maker API", version="0.3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve uploaded images
STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")


@app.on_event("startup")
def on_startup():
    init_db()

<<<<<<< HEAD
=======
# serve files under backend/storage/ at /images/*
app.mount(
    "/images",
    StaticFiles(directory=str(crud.STORAGE_ROOT), html=False),
    name="images",
)

def weather_fallback(date):
    season = guess_season(date)
    temp_min, temp_max = temperature_placeholder(season)
    rep_temp = 0.6 * temp_min + 0.4 * temp_max
    return {"rep_temp": rep_temp, "tmin": temp_min, "tmax": temp_max, "precip": 0, "wind": 0}

def guess_season(date: date):
    month = date.month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"

def temperature_placeholder(season: str):
    if season == "winter":
        return (-5, 5)
    elif season == "spring":
        return (5, 15)
    elif season == "summer":
        return (20, 30)
    elif season == "fall":
        return (15, 20)
    else:
        return (10, 20)  # all-season

def get_weather(city: str, date: date, time_bucket: str = "evening"):
    # Get coordinates for city
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
    geo_result = requests.get(geo_url, params=geo_params).json()
    if not geo_result.get("results"):
        return f"City '{city}' not found"
    lat = geo_result["results"][0]["latitude"]
    lon = geo_result["results"][0]["longitude"]

    # Get weather forecast for coordinates and date
    weather_url = "https://api.open-meteo.com/v1/forecast"
    if time_bucket == "all_day":
        weather_params = {"latitude": lat, "longitude": lon, "daily": "temperature_2m_max,temperature_2m_min", "start_date": date.isoformat(), "end_date": date.isoformat(), "timezone": "auto"}
        weather_result = requests.get(weather_url, params=weather_params).json()
        daily = weather_result.get("daily", {})
        if daily and "time" in daily and date.isoformat() in daily["time"]:
            idx = daily["time"].index(date.isoformat())
            temp_max = daily["temperature_2m_max"][idx]
            temp_min = daily["temperature_2m_min"][idx]
            precip = daily.get("precipitation_probability_max", [0])[idx]
            wind = daily.get("windspeed_10m_max", [0])[idx]
            rep_temp = 0.6 * temp_min + 0.4 * temp_max
            text = f"Weather in {city} on {date}: High {temp_max}°C, Low {temp_min}°C"
            return {"rep_temp": rep_temp, "tmin": temp_min, "tmax": temp_max, "precip": precip, "wind": wind}
        else:
            return weather_fallback(date)
    else:
        hour_map = {"morning": 9, "afternoon": 15, "evening": 19}
        hour = hour_map.get(time_bucket, 12)
        weather_params = {"latitude": lat, "longitude": lon, "hourly": "temperature_2m,precipitation_probability,windspeed_10m", "start_date": date.isoformat(), "end_date": date.isoformat(), "timezone": "auto"}
        weather_result = requests.get(weather_url, params=weather_params).json()
        hourly = weather_result.get("hourly", {})
        if hourly and "time" in hourly:
            # Find index for the requested hour
            for idx, t in enumerate(hourly["time"]):
                if t.endswith(f"T{hour:02d}:00"):
                    temp = hourly["temperature_2m"][idx]
                    precip = hourly.get("precipitation_probability", [0])[idx]
                    wind = hourly.get("windspeed_10m", [0])[idx]
                    return {"rep_temp": temp, "tmin": temp, "tmax": temp, "precip": precip, "wind": wind}
        # Fallback for hourly
        return weather_fallback(date)

"""def temp_to_season(rep_temp: float) -> str:
    if rep_temp < 10:
        return "winter"
    elif 10 <= rep_temp < 15:
        return "fall"
    elif 15 <= rep_temp < 20:
        return "spring"
    else:
        return "summer"

clothing_season = temp_to_season(weather_data["rep_temp"])
"""
# ---------- Users ----------
@app.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    return crud.create_user(session, payload.name, payload.gender, payload.city, payload.style_preferences)
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027

# ---- Users ----
@app.get("/users", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    return crud.list_users(session)

<<<<<<< HEAD


FORMALITY_ORDER = ["casual", "smart_casual", "semi_formal", "formal"]


def _formality_rank(val: Optional[str]) -> int:
    if not val:
        return 0
    try:
        return FORMALITY_ORDER.index(val)
    except ValueError:
        return 0



@app.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    try:
        # NOTE: no gender here anymore
        user = crud.create_user(
            session,
            payload.name,
            payload.city,
            payload.style_preferences,
        )
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---- Items ----
=======
@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, session: Session = Depends(get_session)):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(session, user, **payload.model_dump(exclude_none=True))

@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(session, user)
    return {"ok": True}

# ---------- Items ----------
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
@app.post("/users/{user_id}/items", response_model=ItemRead)
async def upload_item(
    user_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # file type guard
    filename_lower = (file.filename or "").lower()
    if not any(filename_lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP images are allowed")

    content = await file.read()
    item = crud.create_item_with_file(session, user_id, file.filename, content)

    print(
        "auto_classify_on_upload =",
        settings.auto_classify_on_upload,
        "openai_key?",
        bool(settings.openai_api_key),
    )

    # optional auto-classify
    if settings.auto_classify_on_upload:
        try:
            abs_path = (STORAGE_DIR / item.image_url).resolve()
            pred = classify_image(str(abs_path))
            print(pred)
            item = crud.update_item_classification(session, item.id, pred)
            print(item)
        except Exception as e:
            print("auto-classify failed:", e)

    return item


@app.get("/users/{user_id}/items", response_model=List[ItemRead])
def list_items(user_id: int, session: Session = Depends(get_session)):
    return crud.list_items_for_user(session, user_id)


@app.patch("/items/{item_id}", response_model=ItemRead)
def patch_item(item_id: int, payload: ItemUpdate, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return crud.update_item(session, item, **payload.dict(exclude_unset=True))


@app.delete("/items/{item_id}")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    crud.delete_item(session, item)
    return {"ok": True}

<<<<<<< HEAD

# ---- on-demand classification ----
@app.post("/items/{item_id}/classify", response_model=ItemRead)
def classify_item(item_id: int, session: Session = Depends(get_session)):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.image_url:
        raise HTTPException(status_code=400, detail="Item has no image")

    abs_path = (STORAGE_DIR / item.image_url).resolve()
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")

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


# ---- rule-based outfit suggestions ----
def _fits_season(item, season: Optional[str]) -> bool:
    item_season = getattr(item, "season", None)

    # if user didn't filter, or explicitly chose "all season", don't limit by season
    if not season or season in ("any", "all_season") or item_season is None:
        return True

    # direct match
    if item_season == season:
        return True

    # all_season always matches
    if item_season == "all_season":
        return True

    # handle combos like fall_winter, spring_summer
    if "_" in item_season:
        s1, s2 = item_season.split("_")
        return season in (s1, s2)

    return False




def _fits_formality(item, desired: Optional[str]) -> bool:
    item_form = getattr(item, "formality", None)

    # if user didn't filter, everything is allowed
    if not desired or desired == "any":
        return True

    # if item has no formality yet, don't block it completely
    if item_form is None:
        return True

    r_item = _formality_rank(item_form)
    r_desired = _formality_rank(desired)

    # allow items within 1 step of the requested level
    # e.g. smart_casual with semi_formal, semi_formal with formal
    return abs(r_item - r_desired) <= 1



def _color_key(c: Optional[str]) -> str:
    return (c or "").lower().strip()


def _compatible(top, bottom) -> bool:
    if not top or not bottom:
        return True

    # 1) style / formality compatibility
    # avoid very casual tops (hoodies, graphic tees, etc) with very formal bottoms
    try:
        t_form = getattr(top, "formality", None)
        b_form = getattr(bottom, "formality", None)
        if t_form == "casual" and b_form in ("semi_formal", "formal"):
            return False
    except Exception:
        # if anything is missing, just fall back to color logic
        pass

    # 2) color compatibility
    t = _color_key(getattr(top, "primary_color", None))
    b = _color_key(getattr(bottom, "primary_color", None))
    neutrals = {"black", "white", "gray", "grey", "navy", "beige", "tan", "cream"}

    if t == "multicolor" or b == "multicolor":
        return True
    if t == b and t not in neutrals:
        # strongly avoid bright top + same bright bottom (e.g. red + red)
        return False

    return True



def _parse_id_list(raw: Optional[str]) -> set[int]:
    """Parse a comma-separated list of IDs from the query string into a set of ints."""
    if not raw:
        return set()
    out: set[int] = set()
    for chunk in str(raw).split(","):
        piece = chunk.strip()
        if not piece:
            continue
        try:
            out.add(int(piece))
        except ValueError:
            continue
    return out


@app.get("/users/{user_id}/outfits/suggest")
def suggest_outfit(
    user_id: int,
    season: Optional[str] = None,      # "winter","summer","spring","fall","all_season","any"
    formality: Optional[str] = None,   # "casual","smart_casual","semi_formal","formal","any"
    anchor_ids: Optional[str] = None,  # e.g. "12,15" -> items we MUST try to include
    exclude_ids: Optional[str] = None, # e.g. "3,4"  -> items we MUST NOT use
    session: Session = Depends(get_session),
):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    all_items = crud.list_items_for_user(session, user_id)

    # 1) apply exclude list up front
    exclude_set = _parse_id_list(exclude_ids)
    items = [i for i in all_items if i.id not in exclude_set]

    # 2) figure out which remaining items are anchored / must-wear
    anchor_set = _parse_id_list(anchor_ids)
    anchor_items = [i for i in items if i.id in anchor_set]

    anchor_top = next((i for i in anchor_items if i.outfit_part == "top"), None)
    anchor_bottom = next((i for i in anchor_items if i.outfit_part == "bottom"), None)
    anchor_outer = next((i for i in anchor_items if i.outfit_part == "outerwear"), None)
    anchor_shoes = next((i for i in anchor_items if i.outfit_part == "shoes"), None)

    # 3) build filtered pools for everything else (anchors bypass filters)
    def _pool(part: str):
        return [
            i for i in items
            if i.outfit_part == part
            and _fits_season(i, season)
            and _fits_formality(i, formality)
            and i.id not in anchor_set
        ]

    tops = _pool("top")
    bottoms = _pool("bottom")
    outers = _pool("outerwear")
    shoes = _pool("shoes")

    # add a bit of randomness so repeated "Generate" clicks can explore
    # different valid combinations instead of always picking the same first match
    random.shuffle(tops)
    random.shuffle(bottoms)
    random.shuffle(outers)
    random.shuffle(shoes)


    def _want_outer() -> bool:
        return season in ("winter", "fall") or formality in ("semi_formal", "formal")

    def _pick_first():
        # start with anchors if present
        t = anchor_top
        b = anchor_bottom
        o = anchor_outer
        s = anchor_shoes

        # case 1: anchored top + bottom already chosen, just optionally fill outer + shoes
        if t and b:
            if not o and outers and _want_outer():
                o = outers[0]
            if not s and shoes:
                s = shoes[0]
            return {"top": t, "bottom": b, "outer": o, "shoes": s}

        # case 2: anchored top only -> find a compatible bottom
        if t and not b:
            if bottoms:
                # try to respect color compatibility first
                chosen = None
                for cand in bottoms:
                    if _compatible(t, cand):
                        chosen = cand
                        break
                b = chosen or bottoms[0]
            if not o and outers and _want_outer():
                o = outers[0]
            if not s and shoes:
                s = shoes[0]
            return {"top": t, "bottom": b, "outer": o, "shoes": s}

        # case 3: anchored bottom only -> find a compatible top
        if b and not t:
            if tops:
                chosen = None
                for cand in tops:
                    if _compatible(cand, b):
                        chosen = cand
                        break
                t = chosen or tops[0]
            if not o and outers and _want_outer():
                o = outers[0]
            if not s and shoes:
                s = shoes[0]
            return {"top": t, "bottom": b, "outer": o, "shoes": s}

        # case 4: no anchored top/bottom -> fall back to old behavior
        if tops and bottoms:
            for t_candidate in tops:
                for b_candidate in bottoms:
                    if not _compatible(t_candidate, b_candidate):
                        continue
                    t = t_candidate
                    b = b_candidate
                    if not o and outers and _want_outer():
                        o = outers[0]
                    if not s and shoes:
                        s = shoes[0]
                    return {"top": t, "bottom": b, "outer": o, "shoes": s}

            # no color-compatible combo, but we still have tops + bottoms
            t = tops[0]
            b = bottoms[0]
            if not o and outers and _want_outer():
                o = outers[0]
            if not s and shoes:
                s = shoes[0]
            return {"top": t, "bottom": b, "outer": o, "shoes": s}

        # case 5: extreme fallback — no proper top/bottom pools,
        # but we may still have anchors or singles
        if not t and tops:
            t = tops[0]
        if not b and bottoms:
            b = bottoms[0]
        if not o and outers and _want_outer():
            o = outers[0]
        if not s and shoes:
            s = shoes[0]

        return {"top": t, "bottom": b, "outer": o, "shoes": s}

    outfit = _pick_first()

    def _pack(it):
        if not it:
            return None
        return {
            "id": it.id,
            "category": it.category,
            "outfit_part": it.outfit_part,
            "primary_color": it.primary_color,
            "formality": it.formality,
            "season": it.season,
            "image_url": it.image_url,
        }

    return {k: _pack(v) for k, v in outfit.items()}



# ---- debug ----
@app.get("/debug/env")
def debug_env():
    return {
        "auto_classify_on_upload": settings.auto_classify_on_upload,
        "has_openai_key": bool(settings.openai_api_key),
    }
=======
# ---------- Outfits ----------
@app.post("/users/{user_id}/outfits", response_model=OutfitRead)
def create_outfit(user_id: int, payload: OutfitCreate, session: Session = Depends(get_session)):
    if not crud.get_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_outfit(session, user_id, **payload.model_dump(exclude_none=True))

@app.get("/users/{user_id}/outfits", response_model=List[OutfitRead])
def list_outfits(user_id: int, session: Session = Depends(get_session)):
    if not crud.get_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return crud.list_outfits(session, user_id)

@app.get("/outfits/{outfit_id}", response_model=OutfitRead)
def get_outfit(outfit_id: int, session: Session = Depends(get_session)):
    outfit = crud.get_outfit(session, outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    return outfit

@app.patch("/outfits/{outfit_id}", response_model=OutfitRead)
def update_outfit(outfit_id: int, payload: OutfitUpdate, session: Session = Depends(get_session)):
    outfit = crud.get_outfit(session, outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    return crud.update_outfit(session, outfit, **payload.model_dump(exclude_none=True))

@app.delete("/outfits/{outfit_id}")
def delete_outfit(outfit_id: int, session: Session = Depends(get_session)):
    outfit = crud.get_outfit(session, outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    crud.delete_outfit(session, outfit)
    return {"ok": True}

# ---------- Feedback ----------
@app.post("/outfits/{outfit_id}/feedback", response_model=FeedbackRead)
def create_feedback(outfit_id: int, payload: FeedbackCreate, session: Session = Depends(get_session)):
    outfit = crud.get_outfit(session, outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    return crud.create_feedback(session, payload.user_id, outfit_id, payload.score)

@app.get("/outfits/{outfit_id}/feedback", response_model=List[FeedbackRead])
def list_feedback_for_outfit(outfit_id: int, session: Session = Depends(get_session)):
    return crud.list_feedback(session, outfit_id=outfit_id)

@app.get("/feedback/{feedback_id}", response_model=FeedbackRead)
def get_feedback(feedback_id: int, session: Session = Depends(get_session)):
    feedback = crud.get_feedback(session, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback

@app.patch("/feedback/{feedback_id}", response_model=FeedbackRead)
def update_feedback(feedback_id: int, payload: FeedbackUpdate, session: Session = Depends(get_session)):
    feedback = crud.get_feedback(session, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return crud.update_feedback(session, feedback, **payload.model_dump(exclude_none=True))

@app.delete("/feedback/{feedback_id}")
def delete_feedback(feedback_id: int, session: Session = Depends(get_session)):
    feedback = crud.get_feedback(session, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    crud.delete_feedback(session, feedback)
    return {"ok": True}

# --- Filtering functions ---
def filter_by_weather(items, rep_temp, precip=0, wind=0):
    """Filter items by computed season from weather (with nudges)."""
    if rep_temp < 8:
        season = "winter"
    elif rep_temp < 18:
        season = "fall"
    elif rep_temp < 24:
        season = "spring"
    else:
        season = "summer"
    if (precip >= 50 or wind >= 30) and rep_temp < 18:
        if season == "fall":
            season = "winter"
        elif season == "spring":
            season = "fall"
    return [item for item in items if getattr(item, "season", None) in (season, "all-season")]

def filter_by_formality(items, formality):
    """Filter items by formality (e.g., 'casual', 'formal')."""
    if not formality:
        return items
    return [item for item in items if getattr(item, "formality", None) == formality]

def filter_by_gender(items, gender):
    """Filter items by target_gender (e.g., 'male', 'female', 'unisex')."""
    if not gender:
        return items
    gender = gender.lower()
    return [item for item in items if getattr(item, "target_gender", "unisex").lower() in (gender, "unisex")]

def get_filtered_items(items, rep_temp, precip=0, wind=0, formality=None, user_choices=None, gender=None):
    """
    Apply all filters in sequence: weather, formality, user choices, gender.
    Returns the filtered list of items.
    """
    filtered = filter_by_weather(items, rep_temp, precip, wind)
    filtered = filter_by_formality(filtered, formality)
    filtered = filter_by_user_choice(filtered, user_choices)
    filtered = filter_by_gender(filtered, gender)
    return filtered


# ---------- Outfit Suggestion Endpoint ----------
from fastapi import Query

"""
@app.get("/users/{user_id}/suggested-outfit", response_model=List[ItemRead])
def suggest_outfit(
    user_id: int,
    date_: date = Query(default_factory=date.today, alias="date"),
    time_bucket: str = Query("morning", enum=["morning", "afternoon", "evening", "all_day"]),
    formality: str = Query(None),
    session: Session = Depends(get_session),
):
    Suggest an outfit for a user based on weather, formality, and user profile.

    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    items = crud.list_items(session, user_id)
    if not items:
        raise HTTPException(status_code=404, detail="No items found for user")
    weather = get_weather(user.city, date_, time_bucket)
    if isinstance(weather, str):
        raise HTTPException(status_code=400, detail=weather)
    filtered_items = get_filtered_items(
        items,
        rep_temp=weather["rep_temp"],
        precip=weather.get("precip", 0),
        wind=weather.get("wind", 0),
        formality=formality,
        user_choices=None,  # Extend as needed
        gender=user.gender if hasattr(user, "gender") else None,
    )
    return filtered_items
"""
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
