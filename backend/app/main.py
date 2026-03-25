import random
import requests
import hashlib
from datetime import date, datetime
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from typing import List, Optional
from pathlib import Path

from .db import init_db, get_session
from .schemas import UserCreate, UserRead, UserUpdate, ItemRead, ItemUpdate, SignupRequest, LoginRequest, TokenResponse
from . import crud
from .config import settings
from .vision import classify_image
from .aimodel import score_outfit_ml
from .models import User, OutfitHistory, LikedOutfit, DislikedOutfit
from .services.gap_recommendations import compute_gap_recommendations
from .aimodel import score_outfit_ml, extract_features, hue_distance, trained_model
from .auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi import Query

import os

app = FastAPI(title="Outfit Maker API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve uploaded images
STORAGE_DIR = Path(os.getenv("STORAGE_ROOT", "/data/storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")


def _migrate_formality_values() -> None:
    """
    One-time idempotent migration: normalize legacy formality values in the
    Item table to the 3-level system (casual / smart_casual / polished).
    Runs at startup before any ORM reads so SQLModel never sees removed enum
    values.
    """
    from sqlalchemy import text
    from .db import engine
    with engine.begin() as conn:
        conn.execute(text("UPDATE item SET formality = 'casual'      WHERE formality = 'sporty'"))
        conn.execute(text("UPDATE item SET formality = 'smart_casual' WHERE formality = 'business_casual'"))
        conn.execute(text("UPDATE item SET formality = 'polished'     WHERE formality IN ('semi_formal', 'formal')"))


def _migrate_add_auth_columns() -> None:
    """Add email and hashed_password columns to the user table if they don't exist."""
    from sqlalchemy import text
    from .db import engine
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(\"user\")"))
        existing_cols = {row[1] for row in result.fetchall()}

        if "email" not in existing_cols:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN email TEXT'))
            print("✓ Migration: added email column to user table")

        if "hashed_password" not in existing_cols:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN hashed_password TEXT'))
            print("✓ Migration: added hashed_password column to user table")

        # Unique index on email (partial — NULL emails don't conflict)
        conn.execute(text(
            'CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email ON "user"(email) WHERE email IS NOT NULL'
        ))


@app.on_event("startup")
def on_startup():
    init_db()
    _migrate_add_auth_columns()
    _migrate_formality_values()


# ---- Auth ----

@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    email = payload.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(400, "Invalid email address")
    if len(payload.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if not any(c.isdigit() for c in payload.password):
        raise HTTPException(400, "Password must contain at least one number")
    if not payload.city.strip():
        raise HTTPException(400, "City is required")
    if crud.get_user_by_email(session, email):
        raise HTTPException(400, "An account with this email already exists")
    hashed = hash_password(payload.password)
    user = crud.create_user_auth(session, email, hashed, payload.city.strip())
    token = create_access_token(user.id)
    return {"token": token, "user": user}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    email = payload.email.lower().strip()
    user = crud.get_user_by_email(session, email)
    if not user or not user.hashed_password:
        raise HTTPException(401, "Invalid email or password")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(user.id)
    return {"token": token, "user": user}


# ---- Users ----

@app.get("/users/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/users", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    return crud.list_users(session)


FORMALITY_ORDER = ["casual", "smart_casual", "polished"]


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
        user = crud.create_user(
            session,
            payload.name,
            payload.city,
            payload.style_preferences,
        )
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/users/{user_id}", response_model=UserRead)
def update_user_route(
    user_id: int,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated = crud.update_user(session, user, **payload.model_dump(exclude_unset=True))
    return updated


# ---- Items ----

@app.post("/users/{user_id}/items", response_model=ItemRead)
async def upload_item(
    user_id: int,
    file: UploadFile = File(...),
    allow_duplicate: bool = Query(False),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")

    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    filename_lower = (file.filename or "").lower()
    if not any(filename_lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP images are allowed")

    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()

    existing = crud.find_item_by_hash(session, user_id, content_hash)
    if existing and not allow_duplicate:
        raise HTTPException(
            status_code=409,
            detail={
                "reason": "duplicate_item",
                "message": "Item with the same image already exists in this wardrobe.",
                "existing_item_id": existing.id,
            },
        )

    item = crud.create_item_with_file(session, user_id, file.filename, content, content_hash)

    print(
        "auto_classify_on_upload =",
        settings.auto_classify_on_upload,
        "openai_key?",
        bool(settings.openai_api_key),
    )

    if settings.auto_classify_on_upload:
        try:
            abs_path = (STORAGE_DIR / item.image_url).resolve()
            pred = classify_image(str(abs_path))
            print(pred)
            item = crud.update_item_classification(session, item.id, pred)
            print(f"✓ Item classified - Color: {pred.get('color', 'N/A')} | Hex: {pred.get('color_hex', 'N/A')} | HSV: {pred.get('color_hsv', 'N/A')}")
            print(item)
        except Exception as e:
            print("auto-classify failed:", e)

    return item


@app.get("/users/{user_id}/items", response_model=List[ItemRead])
def list_items(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")
    return crud.list_items_for_user(session, user_id)


@app.patch("/items/{item_id}", response_model=ItemRead)
def patch_item(
    item_id: int,
    payload: ItemUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return crud.update_item(session, item, **payload.model_dump(exclude_unset=True))


@app.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    crud.delete_item(session, item)
    return {"ok": True}


# ---- on-demand classification ----

@app.post("/items/{item_id}/classify", response_model=ItemRead)
def classify_item(
    item_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = crud.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    if not item.image_url:
        raise HTTPException(status_code=400, detail="Item has no image")

    abs_path = (STORAGE_DIR / item.image_url).resolve()
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")

    print("CLASSIFY → item:", item_id, "| path:", str(abs_path))
    try:
        pred = classify_image(str(abs_path))
        print("CLASSIFY ← prediction:", pred)
        print(f"✓ Color values - Name: {pred.get('color', 'N/A')} | Hex: {pred.get('color_hex', 'N/A')} | HSV: {pred.get('color_hsv', 'N/A')}")
        updated = crud.update_item_classification(session, item_id, pred)
        return updated
    except Exception as e:
        import traceback
        print("CLASSIFY ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"classification failed: {e}")


# ---- Weather API ----

def _weather_condition_from_code(code: Optional[int]) -> str:
    if code is None:
        return "unknown"
    if code in {0, 1}:
        return "clear"
    if code in {2, 3, 45, 48}:
        return "cloudy"
    if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return "rain"
    if code in {71, 73, 75, 77, 85, 86}:
        return "snow"
    if code in {95, 96, 99}:
        return "storm"
    return "unknown"


def get_weather(city: str, target_date: date) -> dict:
    try:
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

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_resp = requests.get(
            weather_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
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
        weather_codes = daily.get("weathercode") or daily.get("weather_code") or []
        weather_code = weather_codes[idx] if idx < len(weather_codes) else None
        weather_condition = _weather_condition_from_code(weather_code)

        temp = temp_min * 0.7 + temp_max * 0.3

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
            "condition": weather_condition,
        }

    except Exception as e:
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
            "condition": "unknown",
        }


# ---- rule-based outfit suggestions ----

def _fits_season(item, season: Optional[str]) -> bool:
    item_season = getattr(item, "season", None)
    if not season or season in ("any", "all_season") or item_season is None:
        return True
    if item_season == season:
        return True
    if item_season == "all_season":
        return True
    if "_" in item_season:
        s1, s2 = item_season.split("_")
        return season in (s1, s2)
    return False


def _fits_formality(item, desired: Optional[str]) -> bool:
    item_form = getattr(item, "formality", None)
    if not desired or desired == "any":
        return True
    if item_form is None:
        return True
    r_item = _formality_rank(item_form)
    r_desired = _formality_rank(desired)
    return abs(r_item - r_desired) <= 1


def _color_key(c: Optional[str]) -> str:
    return (c or "").lower().strip()


COLOR_HEX_MAP = {
    "black": "#000000", "white": "#ffffff", "gray": "#808080", "grey": "#808080",
    "navy": "#000080", "blue": "#0000ff", "light blue": "#87ceeb", "dark blue": "#00008b",
    "red": "#ff0000", "dark red": "#8b0000", "burgundy": "#800020", "green": "#008000",
    "dark green": "#006400", "olive": "#808000", "yellow": "#ffff00", "orange": "#ffa500",
    "brown": "#a52a2a", "beige": "#f5f5dc", "tan": "#d2b48c", "cream": "#fffdd0",
    "pink": "#ffc0cb", "purple": "#800080", "lavender": "#e6e6fa", "maroon": "#800000",
    "teal": "#008080", "khaki": "#f0e68c", "ivory": "#fffff0", "gold": "#ffd700",
    "silver": "#c0c0c0", "multicolor": "#808080",
}


def hex_to_hsl(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    c_max = max(r, g, b)
    c_min = min(r, g, b)
    delta = c_max - c_min
    l = (c_max + c_min) / 2.0
    if delta == 0:
        return 0.0, 0.0, l
    s = delta / (1 - abs(2 * l - 1))
    if c_max == r:
        h = 60 * (((g - b) / delta) % 6)
    elif c_max == g:
        h = 60 * (((b - r) / delta) + 2)
    else:
        h = 60 * (((r - g) / delta) + 4)
    return h, s, l


def hue_distance(h1: float, h2: float) -> float:
    d = abs(h1 - h2)
    return min(d, 360 - d)


def is_neutral_fallback(h: float, s: float, l: float) -> bool:
    if s < 0.18:
        return True
    if 200 <= h <= 260 and l < 0.35 and s < 0.6:
        return True
    if 10 <= h <= 70 and s < 0.65 and 0.2 <= l <= 0.9:
        return True
    return False


def score_outfit_colors(color_names: list[str]) -> float:
    colors = [c for c in color_names if c]
    if len(colors) < 2:
        return 5.0
    hex_colors = []
    for color_name in colors:
        key = _color_key(color_name)
        hex_val = COLOR_HEX_MAP.get(key, "#808080")
        hex_colors.append(hex_val)
    hsl_colors = [hex_to_hsl(c) for c in hex_colors]
    neutrals = 0
    brights = 0
    has_light = False
    has_dark = False
    hues = []
    has_navy = False
    has_white = False
    earth_tones = 0

    for i, (h, s, l) in enumerate(hsl_colors):
        color_name = _color_key(colors[i])
        if color_name in (
            "black","white","grey","gray","navy","brown",
            "beige","tan","khaki","cream","ivory",
            "olive","silver","multicolor"
        ):
            neutrals += 1
        elif is_neutral_fallback(h, s, l):
            neutrals += 1
        if (
            s > 0.65 and 0.25 < l < 0.8
            and color_name not in ("khaki","beige","tan","brown","olive","navy")
        ):
            brights += 1
        if l > 0.7:
            has_light = True
        if l < 0.3:
            has_dark = True
        hues.append(h)
        if color_name == "navy":
            has_navy = True
        if color_name in ("white", "cream", "ivory"):
            has_white = True
        if color_name in ("beige", "tan", "brown", "khaki", "olive"):
            earth_tones += 1

    score = 0.0
    n = len(colors)
    if n <= 3:
        if neutrals >= 2:
            score += 3
        elif neutrals == 1:
            score += 2
    else:
        if neutrals >= 3:
            score += 4
        elif neutrals == 2:
            score += 3
        elif neutrals == 1:
            score += 1
    if brights <= 1:
        score += 3
    elif brights == 2:
        score += 1
    if has_light and has_dark:
        score += 2
    complementary = False
    analogous = False
    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            d = hue_distance(hues[i], hues[j])
            if d <= 30:
                analogous = True
            if 150 <= d <= 210:
                complementary = True
    if analogous:
        score += 1
    if complementary:
        score += 1
    if earth_tones >= 2 and neutrals >= 2:
        score += 1.5
    if has_navy and has_white and neutrals >= 2:
        score += 1
    return round(min(score, 10.0), 1)


def _get_color_score(top_color, bottom_color, outer_color=None, shoes_color=None) -> float:
    colors = [top_color, bottom_color, outer_color, shoes_color]
    return score_outfit_colors(colors)


def _compatible(top, bottom, outer=None, shoes=None) -> bool:
    pieces = [p for p in (top, bottom, outer, shoes) if p is not None]
    ranked_pieces = [
        _formality_rank(getattr(p, "formality", None))
        for p in pieces
        if getattr(p, "formality", None) is not None
    ]
    if len(ranked_pieces) < 2:
        return True
    return (max(ranked_pieces) - min(ranked_pieces)) <= 1


def _season_penalty(item, season: Optional[str]) -> float:
    if not season or season in ("any", "all_season"):
        return 0.0
    item_season = getattr(item, "season", None)
    if item_season is None or item_season == "all_season":
        return 0.0
    if item_season == season:
        return 0.0
    if "_" in item_season:
        parts = item_season.split("_")
        if season in parts:
            return 0.0
        return 1.0
    ORDER = ["spring", "summer", "fall", "winter"]
    try:
        idx_item = ORDER.index(item_season)
        idx_want = ORDER.index(season)
    except ValueError:
        return 1.0
    dist = min(abs(idx_item - idx_want), 4 - abs(idx_item - idx_want))
    return float(dist)


def _formality_penalty(item, formality: Optional[str]) -> float:
    if not formality or formality == "any":
        return 0.0
    item_form = getattr(item, "formality", None)
    if item_form is None:
        return 0.0
    r_item = _formality_rank(item_form)
    r_want = _formality_rank(formality)
    dist = abs(r_item - r_want)
    return float(dist)


def _score_outfit(top, bottom, outer, shoes, season, formality, verbose: bool = True) -> float:
    top_color  = getattr(top,    "primary_color",     None) if top    else None
    bottom_color = getattr(bottom, "primary_color",   None) if bottom else None
    outer_color  = getattr(outer,  "primary_color",   None) if outer  else None
    shoes_color  = getattr(shoes,  "primary_color",   None) if shoes  else None
    top_sec    = getattr(top,    "secondary_color", None) if top    else None
    bottom_sec = getattr(bottom, "secondary_color", None) if bottom else None
    outer_sec  = getattr(outer,  "secondary_color", None) if outer  else None
    shoes_sec  = getattr(shoes,  "secondary_color", None) if shoes  else None
    all_colors = [c for c in [
        top_color, bottom_color, outer_color, shoes_color,
        top_sec, bottom_sec, outer_sec, shoes_sec,
    ] if c]
    top_hsv    = getattr(top,    "primary_color_hsv", None) if top    else None
    bottom_hsv = getattr(bottom, "primary_color_hsv", None) if bottom else None
    outer_hsv  = getattr(outer,  "primary_color_hsv", None) if outer  else None
    shoes_hsv  = getattr(shoes,  "primary_color_hsv", None) if shoes  else None
    can_use_model = (top_hsv is not None and bottom_hsv is not None)
    if can_use_model:
        color_score = score_outfit_ml(
            colors=all_colors,
            hsvs=[top_hsv, bottom_hsv, outer_hsv, shoes_hsv],
            verbose=verbose,
        )
    else:
        if verbose:
            print(f"⚠️  Missing HSV (top={top_hsv}, bottom={bottom_hsv}) → rule-based fallback")
        color_score = score_outfit_colors(all_colors)
    penalty = 0.0
    for piece in (top, bottom, outer, shoes):
        if piece is None:
            continue
        penalty += _formality_penalty(piece, formality)
    piece_ranks = [
        _formality_rank(getattr(p, "formality", None))
        for p in (top, bottom, outer, shoes)
        if p is not None and getattr(p, "formality", None) is not None
    ]
    if len(piece_ranks) >= 2:
        spread = max(piece_ranks) - min(piece_ranks)
        penalty += spread * 0.5
    final = color_score - penalty
    if verbose and penalty > 0:
        print(f"   🔻 Season/formality penalty: −{penalty:.1f}  "
              f"(color {color_score:.1f} → final {final:.1f})")
    return final


def _outfit_color_fingerprint(outfit: dict) -> str:
    colors = sorted(
        c for c in (
            getattr(outfit.get("top"),    "primary_color", None),
            getattr(outfit.get("bottom"), "primary_color", None),
            getattr(outfit.get("outer"),  "primary_color", None),
            getattr(outfit.get("shoes"),  "primary_color", None),
        ) if c
    )
    return ",".join(colors)


def _pick_outfit_legacy(
    tops, bottoms, outers, shoes,
    anchor_top, anchor_bottom, anchor_outer, anchor_shoes,
    season, formality,
    liked_fps: set = None,
):
    import itertools, time

    def _want_outer() -> bool:
        if formality == "polished":
            return True
        if season in ("winter", "fall"):
            return True
        return False

    t = anchor_top
    b = anchor_bottom
    o = anchor_outer
    s = anchor_shoes

    outer_pool = outers if _want_outer() else [None]
    shoe_pool  = shoes or [None]

    t_list = [t] if t else tops
    b_list = [b] if b else bottoms
    o_list = [o] if o else outer_pool
    s_list = [s] if s else shoe_pool

    if not t_list or not b_list:
        return {"top": t or (tops[0] if tops else None),
                "bottom": b or (bottoms[0] if bottoms else None),
                "outer": o or (outers[0] if outers and _want_outer() else None),
                "shoes": s or (shoes[0] if shoes else None)}

    MAX_COMBOS = 200
    combos = list(itertools.product(t_list, b_list, o_list, s_list))
    if len(combos) > MAX_COMBOS:
        random.shuffle(combos)
        combos = combos[:MAX_COMBOS]

    start = time.perf_counter()

    compatible_combos = []
    feature_rows = []
    fallback_indices = []

    for tc, bc, oc, sc in combos:
        if not _compatible(tc, bc, oc, sc):
            continue
        top_hsv    = getattr(tc, "primary_color_hsv", None) if tc else None
        bottom_hsv = getattr(bc, "primary_color_hsv", None) if bc else None
        outer_hsv  = getattr(oc, "primary_color_hsv", None) if oc else None
        shoes_hsv  = getattr(sc, "primary_color_hsv", None) if sc else None
        hsvs = [top_hsv, bottom_hsv, outer_hsv, shoes_hsv]
        compatible_combos.append((tc, bc, oc, sc, hsvs))
        if top_hsv is not None and bottom_hsv is not None:
            feature_rows.append(extract_features(hsvs))
        else:
            feature_rows.append(None)
            fallback_indices.append(len(compatible_combos) - 1)

    ml_indices = [i for i, f in enumerate(feature_rows) if f is not None]
    ml_scores = {}
    if ml_indices and trained_model is not None:
        import warnings, numpy as np
        X = np.array([feature_rows[i] for i in ml_indices])
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="X does not have valid feature names")
            preds = trained_model.predict(X)
        for idx, raw_score in zip(ml_indices, preds):
            ml_scores[idx] = round(max(0.0, min(float(raw_score), 10.0)), 1)

    scored = []
    for i, (tc, bc, oc, sc, hsvs) in enumerate(compatible_combos):
        if i in ml_scores:
            color_score = ml_scores[i]
        else:
            cs = [c for c in [
                  getattr(tc, "primary_color",   None) if tc else None,
                  getattr(bc, "primary_color",   None) if bc else None,
                  getattr(oc, "primary_color",   None) if oc else None,
                  getattr(sc, "primary_color",   None) if sc else None,
                  getattr(tc, "secondary_color", None) if tc else None,
                  getattr(bc, "secondary_color", None) if bc else None,
                  getattr(oc, "secondary_color", None) if oc else None,
                  getattr(sc, "secondary_color", None) if sc else None,
              ] if c]
            color_score = score_outfit_colors(cs)

        penalty = 0.0
        for piece in (tc, bc, oc, sc):
            if piece is None:
                continue
            penalty += _formality_penalty(piece, formality)

        piece_ranks = [
            _formality_rank(getattr(p, "formality", None))
            for p in (tc, bc, oc, sc)
            if p is not None and getattr(p, "formality", None) is not None
        ]
        if len(piece_ranks) >= 2:
            spread = max(piece_ranks) - min(piece_ranks)
            penalty += spread * 0.5

        fp = _outfit_color_fingerprint({"top": tc, "bottom": bc, "outer": oc, "shoes": sc})
        fp_penalized = liked_fps is not None and fp in liked_fps
        if fp_penalized:
            penalty += 10.0

        scored.append({
            "outfit": {"top": tc, "bottom": bc, "outer": oc, "shoes": sc},
            "score": color_score - penalty,
            "color_fingerprint": fp,
            "fp_penalized": fp_penalized,
        })

    elapsed = time.perf_counter() - start
    scored.sort(key=lambda x: x["score"], reverse=True)

    if not scored:
        return []

    def _diff_count(outfit_a, outfit_b):
        """Count how many pieces differ between two outfits by item id."""
        count = 0
        for key in ("top", "bottom", "outer", "shoes"):
            a = outfit_a.get(key)
            b = outfit_b.get(key)
            a_id = getattr(a, "id", None) if a else None
            b_id = getattr(b, "id", None) if b else None
            if a_id != b_id:
                count += 1
        return count

    MIN_PIECE_DIFF = 2
    DIVERSITY_THRESHOLDS = (1.5, 2.0)
    picked = [scored[0]]
    picked_ids = {id(scored[0])}

    for threshold in DIVERSITY_THRESHOLDS:
        natural = next((e for e in scored if id(e) not in picked_ids), None)
        # require at least MIN_PIECE_DIFF different pieces vs every already-picked outfit
        diverse = next(
            (e for e in scored
             if id(e) not in picked_ids
             and all(_diff_count(e["outfit"], p["outfit"]) >= MIN_PIECE_DIFF for p in picked)),
            None,
        )
        if natural is None:
            break
        if diverse is None or diverse["score"] < natural["score"] - threshold:
            picked.append(natural)
        else:
            picked.append(diverse)
        picked_ids.add(id(picked[-1]))

    picked_set = set(id(e) for e in picked)

    print(f"\n⚡ Evaluated {len(scored)} compatible combos in {elapsed:.2f}s")
    if liked_fps:
        print(f"🚫 Avoided fingerprints ({len(liked_fps)}):")
        for afp in sorted(liked_fps):
            print(f"   · {afp}")
    print(f"\n{'─'*120}")
    print(f"{'Rank':>4}  {'Score':>6}  {'Top':<22} {'Bottom':<22} {'Outer':<22} {'Shoes':<22} {'Fingerprint'}")
    print(f"{'─'*120}")

    def _fmt(piece):
        if not piece:
            return "-"
        cat = getattr(piece, "category", None) or getattr(piece, "outfit_part", "?")
        form = getattr(piece, "formality", "?") or "?"
        return f"{cat}({form})"

    for i, entry in enumerate(scored, 1):
        o = entry["outfit"]
        marker = " ◀ PICKED" if id(entry) in picked_set else ""
        penalty_marker = " 🚫-10" if entry.get("fp_penalized") else ""
        print(
            f"  #{i:>3}  {entry['score']:>5.1f}  "
            f"{_fmt(o.get('top')):<22} "
            f"{_fmt(o.get('bottom')):<22} "
            f"{_fmt(o.get('outer')):<22} "
            f"{_fmt(o.get('shoes')):<22} "
            f"{entry.get('color_fingerprint','')}"
            f"{penalty_marker}{marker}"
        )
    print(f"{'─'*120}")

    print(f"\n🏆 Top 3 — detailed breakdown:\n")
    for i, item in enumerate(picked, 1):
        o_part = item["outfit"]
        fp = item.get("color_fingerprint", "")
        print(f"  #{i}  score={item['score']:.1f}  colors={fp}  "
              f"T={o_part['top'].category if o_part['top'] else '-'}  "
              f"B={o_part['bottom'].category if o_part['bottom'] else '-'}  "
              f"O={o_part['outer'].category if o_part['outer'] else '-'}  "
              f"S={o_part['shoes'].category if o_part['shoes'] else '-'}")
        _score_outfit(o_part['top'], o_part['bottom'], o_part['outer'], o_part['shoes'],
                      season, formality, verbose=True)

    return picked


def _parse_id_list(raw: Optional[str]) -> set[int]:
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


def _enum_or_str(value) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _snapshot_fields(item, prefix: str) -> dict:
    return {
        f"{prefix}_category": _enum_or_str(getattr(item, "category", None)) if item else None,
        f"{prefix}_color": _enum_or_str(getattr(item, "primary_color", None)) if item else None,
        f"{prefix}_season": _enum_or_str(getattr(item, "season", None)) if item else None,
        f"{prefix}_formality": _enum_or_str(getattr(item, "formality", None)) if item else None,
    }


def _save_outfit_history(
    session: Session,
    user_id: int,
    requested_date: date,
    city: str,
    weather: dict,
    requested_formality: Optional[str],
    outfit: dict,
) -> OutfitHistory:
    top = outfit.get("top")
    bottom = outfit.get("bottom")
    outer = outfit.get("outer")
    shoes = outfit.get("shoes")
    history = OutfitHistory(
        user_id=user_id,
        requested_date=requested_date,
        city=city,
        weather_temp_c=weather.get("temperature"),
        weather_condition=weather.get("condition"),
        inferred_season=weather.get("season"),
        requested_formality=requested_formality if requested_formality not in (None, "any") else None,
        top_item_id=getattr(top, "id", None),
        bottom_item_id=getattr(bottom, "id", None),
        outerwear_item_id=getattr(outer, "id", None),
        shoes_item_id=getattr(shoes, "id", None),
        **_snapshot_fields(top, "top"),
        **_snapshot_fields(bottom, "bottom"),
        **_snapshot_fields(outer, "outerwear"),
        **_snapshot_fields(shoes, "shoes"),
    )
    session.add(history)
    session.commit()
    session.refresh(history)
    return history


@app.get("/users/{user_id}/outfits/suggest")
def suggest_outfit(
    user_id: int,
    outfit_date: Optional[str] = None,
    formality: Optional[str] = None,
    anchor_ids: Optional[str] = None,
    exclude_ids: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")

    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if not user.city:
        raise HTTPException(400, "User has no city set. Cannot determine weather.")

    if outfit_date:
        try:
            target_date = datetime.strptime(outfit_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, f"Invalid date format: {outfit_date}. Use YYYY-MM-DD")
    else:
        target_date = date.today()

    weather = get_weather(user.city, target_date)
    season = weather["season"]

    print(f"📍 {weather['city']} on {target_date}")
    print(f"🌡️  Temperature: {weather['temperature']}°C (range: {weather['temp_min']}-{weather['temp_max']}°C)")
    print(f"🍂 Clothing season: {season}")

    all_items = crud.list_items_for_user(session, user_id)
    exclude_set = _parse_id_list(exclude_ids)
    items = [i for i in all_items if i.id not in exclude_set]
    anchor_set = _parse_id_list(anchor_ids)
    anchor_items = [i for i in items if i.id in anchor_set]
    anchor_top = next((i for i in anchor_items if i.outfit_part == "top"), None)
    anchor_bottom = next((i for i in anchor_items if i.outfit_part == "bottom"), None)
    anchor_outer = next((i for i in anchor_items if i.outfit_part == "outerwear"), None)
    anchor_shoes = next((i for i in anchor_items if i.outfit_part == "shoes"), None)

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

    print(f"🔍 Filtered pools for formality='{formality}', season='{season}':")
    print(f"   Tops: {len(tops)} items")
    print(f"   Bottoms: {len(bottoms)} items")
    print(f"   Outers: {len(outers)} items")
    print(f"   Shoes: {len(shoes)} items")

    for item in all_items:
        if item.outfit_part == "top" and item not in tops and item.id not in anchor_set and item.id not in exclude_set:
            print(f"   ❌ Top filtered: {item.category} (season={item.season}, formality={item.formality})")
        if item.outfit_part == "bottom" and item not in bottoms and item.id not in anchor_set and item.id not in exclude_set:
            print(f"   ❌ Bottom filtered: {item.category} (season={item.season}, formality={item.formality})")

    random.shuffle(tops)
    random.shuffle(bottoms)
    random.shuffle(outers)
    random.shuffle(shoes)

    liked_fps = set(
        row.color_fingerprint
        for row in session.exec(
            select(LikedOutfit).where(LikedOutfit.user_id == user_id)
        ).all()
        if row.color_fingerprint
    )
    disliked_fps = set(
        row.color_fingerprint
        for row in session.exec(
            select(DislikedOutfit).where(DislikedOutfit.user_id == user_id)
        ).all()
        if row.color_fingerprint
    )
    avoid_fps = liked_fps | disliked_fps

    ranked = _pick_outfit_legacy(
        tops, bottoms, outers, shoes,
        anchor_top, anchor_bottom, anchor_outer, anchor_shoes,
        season, formality,
        liked_fps=avoid_fps,
    )

    if not ranked or not any(
        entry["outfit"].get("top") or entry["outfit"].get("bottom")
        for entry in ranked
    ):
        raise HTTPException(
            status_code=422,
            detail="Not enough compatible clothes in your wardrobe to build an outfit. Try adding more items or adjusting your filters."
        )

    outfit = ranked[0]["outfit"] if ranked else {
        "top": None, "bottom": None, "outer": None, "shoes": None
    }

    def _pack(it):
        if not it:
            return None
        return {
            "id": it.id,
            "category": it.category,
            "outfit_part": it.outfit_part,
            "primary_color": it.primary_color,
            "secondary_color": it.secondary_color,
            "formality": it.formality,
            "season": it.season,
            "image_url": it.image_url,
        }

    packed_outfit = {k: _pack(v) for k, v in outfit.items()}

    _save_outfit_history(
        session=session,
        user_id=user_id,
        requested_date=target_date,
        city=user.city,
        weather=weather,
        requested_formality=formality,
        outfit=outfit,
    )

    outfits = []
    for i, entry in enumerate(ranked, 1):
        ranked_outfit = entry["outfit"]
        fp = entry.get("color_fingerprint") or _outfit_color_fingerprint(ranked_outfit)
        outfits.append({
            "rank": i,
            "score": round(entry["score"], 1),
            "color_fingerprint": fp,
            "already_liked": fp in liked_fps,
            "already_disliked": fp in disliked_fps,
            "outfit": {k: _pack(v) for k, v in ranked_outfit.items()},
        })

    gap_recommendations = compute_gap_recommendations(session, user_id, limit=6)

    return {
        "weather": weather,
        "outfit": packed_outfit,
        "outfits": outfits,
        "gapRecommendations": gap_recommendations,
    }


from pydantic import BaseModel as _PydanticBase


class LikeComboPayload(_PydanticBase):
    color_fingerprint: str


@app.post("/users/{user_id}/liked-combos", status_code=201)
def like_combo(
    user_id: int,
    payload: LikeComboPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    existing = session.exec(
        select(LikedOutfit).where(
            LikedOutfit.user_id == user_id,
            LikedOutfit.color_fingerprint == payload.color_fingerprint,
        )
    ).first()
    if existing:
        return {"status": "already_liked"}
    record = LikedOutfit(user_id=user_id, color_fingerprint=payload.color_fingerprint)
    session.add(record)
    session.commit()
    return {"status": "liked"}


@app.get("/users/{user_id}/disliked-combos")
def list_disliked_combos(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    rows = session.exec(select(DislikedOutfit).where(DislikedOutfit.user_id == user_id)).all()
    return [{"id": r.id, "color_fingerprint": r.color_fingerprint, "created_at": r.created_at} for r in rows]


@app.post("/users/{user_id}/disliked-combos", status_code=201)
def dislike_combo(
    user_id: int,
    payload: LikeComboPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    liked = session.exec(select(LikedOutfit).where(
        LikedOutfit.user_id == user_id,
        LikedOutfit.color_fingerprint == payload.color_fingerprint,
    )).first()
    if liked:
        session.delete(liked)
    existing = session.exec(select(DislikedOutfit).where(
        DislikedOutfit.user_id == user_id,
        DislikedOutfit.color_fingerprint == payload.color_fingerprint,
    )).first()
    if existing:
        session.commit()
        return {"status": "already_disliked"}
    record = DislikedOutfit(user_id=user_id, color_fingerprint=payload.color_fingerprint)
    session.add(record)
    session.commit()
    session.refresh(record)
    return {"status": "disliked", "id": record.id}


@app.delete("/users/{user_id}/disliked-combos")
def undislike_combo(
    user_id: int,
    payload: LikeComboPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    existing = session.exec(select(DislikedOutfit).where(
        DislikedOutfit.user_id == user_id,
        DislikedOutfit.color_fingerprint == payload.color_fingerprint,
    )).first()
    if existing:
        session.delete(existing)
        session.commit()
    return {"status": "undisliked"}


@app.delete("/users/{user_id}/liked-combos")
def unlike_combo(
    user_id: int,
    payload: LikeComboPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    existing = session.exec(
        select(LikedOutfit).where(
            LikedOutfit.user_id == user_id,
            LikedOutfit.color_fingerprint == payload.color_fingerprint,
        )
    ).first()
    if existing:
        session.delete(existing)
        session.commit()
    return {"status": "unliked"}


@app.get("/users/{user_id}/wardrobe/recommendations")
def get_wardrobe_recommendations(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    recommendations = compute_gap_recommendations(session=session, user_id=user_id, limit=6)
    return {"recommendations": recommendations}


# ---- debug ----

@app.get("/debug/env")
def debug_env():
    return {
        "auto_classify_on_upload": settings.auto_classify_on_upload,
        "has_openai_key": bool(settings.openai_api_key),
    }


# ---- Style Lab: score an arbitrary outfit ----

from pydantic import BaseModel as PydanticBaseModel


class ScoreRequest(PydanticBaseModel):
    top_id: Optional[int] = None
    bottom_id: Optional[int] = None
    outer_id: Optional[int] = None
    shoes_id: Optional[int] = None


@app.post("/users/{user_id}/outfits/score")
def score_outfit_endpoint(
    user_id: int,
    payload: ScoreRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(403, "Access denied")

    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    def _get(item_id):
        if not item_id:
            return None
        it = crud.get_item(session, item_id)
        if it and it.user_id != user_id:
            raise HTTPException(403, f"Item {item_id} doesn't belong to this user")
        return it

    top = _get(payload.top_id)
    bottom = _get(payload.bottom_id)
    outer = _get(payload.outer_id)
    shoes = _get(payload.shoes_id)

    if not top and not bottom:
        raise HTTPException(400, "Pick at least a top or bottom")

    colors = [
        getattr(top,    "primary_color",     None) if top    else None,
        getattr(bottom, "primary_color",     None) if bottom else None,
        getattr(outer,  "primary_color",     None) if outer  else None,
        getattr(shoes,  "primary_color",     None) if shoes  else None,
    ]
    hsvs = [
        getattr(top,    "primary_color_hsv", None) if top    else None,
        getattr(bottom, "primary_color_hsv", None) if bottom else None,
        getattr(outer,  "primary_color_hsv", None) if outer  else None,
        getattr(shoes,  "primary_color_hsv", None) if shoes  else None,
    ]

    top_hsv    = hsvs[0]
    bottom_hsv = hsvs[1]
    can_use_model = (top_hsv is not None and bottom_hsv is not None)

    if can_use_model:
        score = score_outfit_ml(colors=colors, hsvs=hsvs, verbose=True)
    else:
        score = score_outfit_colors(colors)

    features = extract_features(hsvs)
    feat_names = [
        "avg_hue_distance", "max_hue_distance", "avg_saturation",
        "high_sat_count", "neutral_count", "has_contrast",
    ]
    feat_dict = dict(zip(feat_names, features))

    explanations = []

    SLOT_NAMES = ["top", "bottom", "outerwear", "shoes"]
    pieces = [top, bottom, outer, shoes]

    formalities = {}
    for i, piece in enumerate(pieces):
        if piece:
            f = getattr(piece, "formality", None)
            if f:
                formalities[SLOT_NAMES[i]] = f

    if len(set(formalities.values())) > 1:
        ranks = {slot: _formality_rank(f) for slot, f in formalities.items()}
        hi_slot = max(ranks, key=ranks.get)
        lo_slot = min(ranks, key=ranks.get)
        gap = ranks[hi_slot] - ranks[lo_slot]
        if gap >= 2:
            explanations.append({
                "type": "style",
                "icon": "👔",
                "message": f"Style mismatch — your {lo_slot} is {formalities[lo_slot]} but {hi_slot} is {formalities[hi_slot]}. They don't belong in the same outfit.",
            })
        elif gap == 1:
            explanations.append({
                "type": "style",
                "icon": "👔",
                "message": f"Slight style gap — {lo_slot} is {formalities[lo_slot]}, {hi_slot} is {formalities[hi_slot]}. It can work but it's a stretch.",
            })

    seasons = {}
    for i, piece in enumerate(pieces):
        if piece:
            s = getattr(piece, "season", None)
            if s and s != "all_season":
                seasons[SLOT_NAMES[i]] = s

    unique_seasons = set(seasons.values())
    if len(unique_seasons) > 1:
        OPPOSITES = {("summer", "winter"), ("winter", "summer"), ("spring", "fall"), ("fall", "spring")}
        season_list = list(seasons.items())
        for a in range(len(season_list)):
            for b in range(a + 1, len(season_list)):
                s_a, s_b = season_list[a], season_list[b]
                if (s_a[1], s_b[1]) in OPPOSITES:
                    explanations.append({
                        "type": "style",
                        "icon": "🌡️",
                        "message": f"Season clash — {s_a[0]} is {s_a[1]} but {s_b[0]} is {s_b[1]}.",
                    })
                    break
            else:
                continue
            break

    parsed = []
    for hsv_str in hsvs:
        if hsv_str:
            try:
                parts = hsv_str.split(",")
                parsed.append((float(parts[0]), float(parts[1]), float(parts[2])))
            except Exception:
                parsed.append(None)
        else:
            parsed.append(None)

    bright_pieces = sum(1 for p in parsed if p and p[1] >= 20)
    neutral_c = int(feat_dict["neutral_count"])

    worst_dist = 0
    worst_pair = None
    for i in range(4):
        for j in range(i + 1, 4):
            if parsed[i] and parsed[j]:
                if parsed[i][1] >= 20 and parsed[j][1] >= 20:
                    d = hue_distance(parsed[i][0], parsed[j][0])
                    if d > worst_dist:
                        worst_dist = d
                        worst_pair = (i, j)

    if worst_pair:
        ci, cj = worst_pair
        c1 = colors[ci] or SLOT_NAMES[ci]
        c2 = colors[cj] or SLOT_NAMES[cj]
        if neutral_c >= 1 and worst_dist > 150:
            explanations.append({
                "type": "clash",
                "icon": "⚠️",
                "message": f"{c1} and {c2} clash — {worst_dist:.0f}° apart, even your neutrals can't save that combo.",
            })
        elif neutral_c == 0 and worst_dist > 100:
            explanations.append({
                "type": "clash",
                "icon": "⚠️",
                "message": f"{c1} and {c2} are {worst_dist:.0f}° apart with no neutrals to balance them out.",
            })
        elif neutral_c == 0 and bright_pieces >= 3 and worst_dist > 60:
            explanations.append({
                "type": "clash",
                "icon": "⚠️",
                "message": f"Too many colors without a neutral anchor — {c1} and {c2} add to the chaos.",
            })

    high_sat = int(feat_dict["high_sat_count"])
    if high_sat >= 3:
        explanations.append({
            "type": "loud",
            "icon": "🔴",
            "message": f"{high_sat} loud pieces — too many bright colors competing with each other.",
        })
    elif high_sat == 2:
        explanations.append({
            "type": "loud",
            "icon": "🟡",
            "message": "2 bright pieces — on the edge of being too busy.",
        })

    neutral_c = int(feat_dict["neutral_count"])
    total_pieces = sum(1 for p in pieces if p is not None)
    if neutral_c == total_pieces and total_pieces >= 2:
        explanations.append({
            "type": "boring",
            "icon": "😴",
            "message": "All neutrals — safe but a bit boring. One accent color would liven it up.",
        })
    elif neutral_c >= 3 and total_pieces >= 4:
        explanations.append({
            "type": "boring",
            "icon": "😐",
            "message": "Mostly neutrals — plays it very safe. A pop of color could help.",
        })

    if not explanations:
        explanations.append({
            "type": "good",
            "icon": "✅",
            "message": "Colors, style, and balance all look good.",
        })

    if score >= 8.0:
        verdict = {"label": "Excellent", "emoji": "🔥", "color": "green"}
    elif score >= 6.5:
        verdict = {"label": "Good", "emoji": "👍", "color": "blue"}
    elif score >= 4.5:
        verdict = {"label": "Okay", "emoji": "😐", "color": "yellow"}
    elif score >= 3.0:
        verdict = {"label": "Poor", "emoji": "👎", "color": "orange"}
    else:
        verdict = {"label": "Clashing", "emoji": "💥", "color": "red"}

    def _pack_item(it):
        if not it:
            return None
        return {
            "id": it.id,
            "category": it.category,
            "outfit_part": it.outfit_part,
            "primary_color": it.primary_color,
            "primary_color_hex": it.primary_color_hex,
            "primary_color_hsv": it.primary_color_hsv,
            "formality": it.formality,
            "season": it.season,
            "image_url": it.image_url,
        }

    return {
        "score": round(score, 1),
        "used_ml": can_use_model,
        "verdict": verdict,
        "features": feat_dict,
        "explanations": explanations,
        "items": {
            "top": _pack_item(top),
            "bottom": _pack_item(bottom),
            "outer": _pack_item(outer),
            "shoes": _pack_item(shoes),
        },
    }
