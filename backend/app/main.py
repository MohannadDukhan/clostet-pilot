import random
import requests
from datetime import date, datetime
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from typing import List, Optional
from pathlib import Path

from .db import init_db, get_session
from .schemas import UserCreate, UserRead, ItemRead, ItemUpdate
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


# ---- Users ----
@app.get("/users", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    return crud.list_users(session)



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


# ---- Weather API ----
def get_weather(city: str, target_date: date) -> dict:
    """
    Get weather forecast using Open-Meteo API.
    Returns temperature and determines appropriate clothing season.
    """
    try:
        # Step 1: Geocode the city
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(
            geo_url,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=5
        )
        geo_data = geo_resp.json()
        
        if not geo_data.get("results"):
            raise ValueError(f"City '{city}' not found")
        
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        
        # Step 2: Get weather forecast
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_resp = requests.get(
            weather_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min",
                "start_date": target_date.isoformat(),
                "end_date": target_date.isoformat(),
                "timezone": "auto"
            },
            timeout=5
        )
        weather_data = weather_resp.json()
        
        daily = weather_data.get("daily", {})
        if not daily or "time" not in daily:
            raise ValueError("Invalid weather response")
        
        idx = daily["time"].index(target_date.isoformat())
        temp_max = daily["temperature_2m_max"][idx]
        temp_min = daily["temperature_2m_min"][idx]
        
        # Representative temperature (weighted toward cooler for outfit planning)
        temp = temp_min * 0.7 + temp_max * 0.3
        
        # Determine clothing season based on actual temperature
        if temp < 5:
            season = "winter"
        elif temp < 12:
            season = "fall"
        elif temp < 20:
            season = "spring"
        else:
            season = "summer"
        
        return {
            "temperature": round(temp, 1),
            "temp_min": temp_min,
            "temp_max": temp_max,
            "season": season,
            "city": city,
        }
    
    except Exception as e:
        # Fallback: use calendar month for Northern Hemisphere
        print(f"Weather API failed: {e}. Using calendar-based fallback.")
        month = target_date.month
        
        if month in [12, 1, 2]:
            season, temp = "winter", 0
        elif month in [3, 4, 5]:
            season, temp = "spring", 12
        elif month in [6, 7, 8]:
            season, temp = "summer", 22
        else:
            season, temp = "fall", 10
        
        return {
            "temperature": temp,
            "temp_min": temp - 5,
            "temp_max": temp + 5,
            "season": season,
            "city": city,
        }


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
    outfit_date: Optional[str] = None,  # date for the outfit (e.g. "2025-11-22")
    formality: Optional[str] = None,    # "casual","smart_casual","semi_formal","formal","any"
    anchor_ids: Optional[str] = None,   # e.g. "12,15" -> items we MUST try to include
    exclude_ids: Optional[str] = None,  # e.g. "3,4"  -> items we MUST NOT use
    session: Session = Depends(get_session),
):
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    if not user.city:
        raise HTTPException(400, "User has no city set. Cannot determine weather.")
    
    # Parse date or use today
    if outfit_date:
        try:
            target_date = datetime.strptime(outfit_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, f"Invalid date format: {outfit_date}. Use YYYY-MM-DD")
    else:
        target_date = date.today()
    
    # Get weather and determine season from actual temperature
    weather = get_weather(user.city, target_date)
    season = weather["season"]
    
    print(f"📍 {weather['city']} on {target_date}")
    print(f"🌡️  Temperature: {weather['temperature']}°C (range: {weather['temp_min']}-{weather['temp_max']}°C)")
    print(f"🍂 Clothing season: {season}")

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
    #print("SUGGESTED OUTFIT:", outfit)

    return {k: _pack(v) for k, v in outfit.items()}



# ---- debug ----
@app.get("/debug/env")
def debug_env():
    return {
        "auto_classify_on_upload": settings.auto_classify_on_upload,
        "has_openai_key": bool(settings.openai_api_key),
    }
