import random
import requests
import hashlib
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
from .aimodel import score_outfit_ml
from fastapi import Query

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
    

@app.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserCreate, session: Session = Depends(get_session)):
    """Allow editing a user's name / city (and optional style preferences)."""
    user = crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = crud.update_user(
        session,
        user,
        name=payload.name,
        city=payload.city,
        style_preferences=payload.style_preferences,
    )
    return updated



# ---- Items ----
@app.post("/users/{user_id}/items", response_model=ItemRead)
async def upload_item(
    user_id: int,
    file: UploadFile = File(...),
    allow_duplicate: bool = Query(False),
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
    content_hash = hashlib.sha256(content).hexdigest()

    existing = crud.find_item_by_hash(session, user_id, content_hash)
    if existing and not allow_duplicate:
        # send a 409 with structured detail so the frontend can show a confirm
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

    # optional auto-classify
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
        print(f"✓ Color values - Name: {pred.get('color', 'N/A')} | Hex: {pred.get('color_hex', 'N/A')} | HSV: {pred.get('color_hsv', 'N/A')}")
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


# Color name to approximate hex mapping
COLOR_HEX_MAP = {
    "black": "#000000",
    "white": "#ffffff",
    "gray": "#808080",
    "grey": "#808080",
    "navy": "#000080",
    "blue": "#0000ff",
    "light blue": "#87ceeb",
    "dark blue": "#00008b",
    "red": "#ff0000",
    "dark red": "#8b0000",
    "burgundy": "#800020",
    "green": "#008000",
    "dark green": "#006400",
    "olive": "#808000",
    "yellow": "#ffff00",
    "orange": "#ffa500",
    "brown": "#a52a2a",
    "beige": "#f5f5dc",
    "tan": "#d2b48c",
    "cream": "#fffdd0",
    "pink": "#ffc0cb",
    "purple": "#800080",
    "lavender": "#e6e6fa",
    "maroon": "#800000",
    "teal": "#008080",
    "khaki": "#f0e68c",
    "ivory": "#fffff0",
    "gold": "#ffd700",
    "silver": "#c0c0c0",
    "multicolor": "#808080",  # treat as neutral
}


def hex_to_hsl(hex_color: str):
    """Convert #rrggbb to (h, s, l). h in [0,360), s,l in [0,1]."""
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
    """Smallest distance between two hues on color wheel."""
    d = abs(h1 - h2)
    return min(d, 360 - d)


def is_neutral_fallback(h: float, s: float, l: float) -> bool:
    """Fallback HSL-based neutral check."""
    # very low saturation (grey/white/black)
    if s < 0.18:
        return True
    # navy-like dark blue
    if 200 <= h <= 260 and l < 0.35 and s < 0.6:
        return True
    # fallback warm earth tones
    if 10 <= h <= 70 and s < 0.65 and 0.2 <= l <= 0.9:
        return True
    return False


def score_outfit_colors(color_names: list[str]) -> float:
    """
    Score color harmony for outfit pieces.
    
    Args:
        color_names: List of 2-4 color names (e.g., ["black", "white", "navy"])
    
    Returns:
        Score from 0-10 (higher = better color harmony)
    """
    # Filter out None values
    colors = [c for c in color_names if c]
    if len(colors) < 2:
        return 5.0  # neutral score if not enough colors
    
    # Convert color names to hex
    hex_colors = []
    for color_name in colors:
        key = _color_key(color_name)
        hex_val = COLOR_HEX_MAP.get(key, "#808080")  # default to gray
        hex_colors.append(hex_val)
    
    # Convert to HSL
    hsl_colors = [hex_to_hsl(c) for c in hex_colors]
    
    neutrals = 0
    brights = 0
    has_light = False
    has_dark = False
    hues = []
    
    # Track specific neutral types for bonuses
    has_navy = False
    has_white = False
    earth_tones = 0  # beige, tan, brown, khaki
    
    for i, (h, s, l) in enumerate(hsl_colors):
        color_name = _color_key(colors[i])
        
        # 1️⃣ NAME-BASED neutrals first (fixes beige/tan/navy/brown)
        if color_name in (
            "black","white","grey","gray","navy","brown",
            "beige","tan","khaki","cream","ivory",
            "olive","silver","multicolor"
        ):
            neutrals += 1
        # fallback HSL neutral
        elif is_neutral_fallback(h, s, l):
            neutrals += 1
        
        # 2️⃣ BRIGHTS — EXCLUDE earth tones + navy from bright counting
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
        
        # Track specific colors for bonuses
        if color_name == "navy":
            has_navy = True
        if color_name in ("white", "cream", "ivory"):
            has_white = True
        if color_name in ("beige", "tan", "brown", "khaki", "olive"):
            earth_tones += 1
    
    score = 0.0
    n = len(colors)
    
    # 1) Neutrals: reward outfits with neutral anchors
    if n <= 3:
        if neutrals >= 2:
            score += 3
        elif neutrals == 1:
            score += 2
    else:  # 4 pieces
        if neutrals >= 3:
            score += 4  # Bonus for 3+ neutrals in 4-piece outfit
        elif neutrals == 2:
            score += 3
        elif neutrals == 1:
            score += 1
    
    # 2) Bright colors: penalize too many loud colors
    if brights <= 1:
        score += 3
    elif brights == 2:
        score += 1
    # else +0 (too many brights)
    
    # 3) Light/dark contrast: reward depth
    if has_light and has_dark:
        score += 2
    
    # 4) Hue harmony on color wheel
    complementary = False
    analogous = False
    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            d = hue_distance(hues[i], hues[j])
            if d <= 30:          # analogous (similar colors)
                analogous = True
            if 150 <= d <= 210:  # complementary (opposite colors)
                complementary = True
    
    if analogous:
        score += 1
    if complementary:
        score += 1
    
    # 5) Bonus for all-neutral earth tone outfits (beige, tan, brown, khaki)
    if earth_tones >= 2 and neutrals >= 2:
        score += 1.5  # Warm earth tones bonus
    
    # 6) Bonus for classic business formal (navy + white + dark neutrals)
    if has_navy and has_white and neutrals >= 2:
        score += 1  # Business formal bonus
    
    return round(min(score, 10.0), 1)


def _get_color_score(top_color, bottom_color, outer_color=None, shoes_color=None) -> float:
    """
    Get color harmony score for outfit pieces.
    
    Args:
        top_color: Color of the top (required)
        bottom_color: Color of the bottom (required)
        outer_color: Color of outer layer (optional)
        shoes_color: Color of shoes (optional)
    
    Returns:
        Score from 0-10 (higher = better color harmony)
    """
    colors = [top_color, bottom_color, outer_color, shoes_color]
    return score_outfit_colors(colors)


def _compatible(top, bottom, outer=None, shoes=None) -> bool:
    """
    Check if outfit pieces are minimally compatible (formality rules only).
    Color scoring is handled separately in _score_outfit.
    """
    if not top or not bottom:
        return True

    # Only check formality compatibility
    # Color scoring happens in _score_outfit, so we don't double-score
    try:
        t_form = getattr(top, "formality", None)
        b_form = getattr(bottom, "formality", None)
        if t_form == "casual" and b_form in ("semi_formal", "formal"):
            return False
    except Exception:
        pass
    
    return True  # If formality is OK, let scoring determine quality


def _score_outfit(top, bottom, outer, shoes, season, formality, verbose: bool = False) -> float:
    """
    Score an outfit based on how well pieces work together.
    Higher score = better outfit.
    
    Args:
        verbose: If True, show detailed ML model output
    
    Factors:
    - Season match: 0-30 points
    - Formality match: 0-40 points
    - Color harmony: 0-30 points (scaled from 0-10 color score)
    """
    score = 0.0
    
    # Season scoring (0-30 points)
    for item in [top, bottom, outer, shoes]:
        if not item:
            continue
        item_season = getattr(item, "season", None)
        if item_season == season:
            score += 10  # Perfect match
        elif item_season == "all_season":
            score += 7   # All-season is versatile
        elif item_season and "_" in item_season:
            s1, s2 = item_season.split("_")
            if season in (s1, s2):
                score += 8  # Combo season match
    
    # Formality scoring (0-40 points) and track mismatches for color penalty
    formality_mismatch_count = 0
    if formality:
        for item in [top, bottom, outer, shoes]:
            if not item:
                continue
            item_form = getattr(item, "formality", None)
            if not item_form:
                continue
            
            desired_rank = _formality_rank(formality)
            item_rank = _formality_rank(item_form)
            diff = abs(desired_rank - item_rank)
            
            if diff == 0:
                score += 10  # Perfect match
            elif diff == 1:
                score += 5   # Close match (one level off)
                formality_mismatch_count += 1  # Track mismatch for color penalty
            # diff >= 2: no points, but count as mismatch
            elif diff >= 2:
                formality_mismatch_count += 1
    
    # Color harmony scoring (0-30 points)
    # Get colors from all pieces
    top_color = getattr(top, "primary_color", None) if top else None
    bottom_color = getattr(bottom, "primary_color", None) if bottom else None
    outer_color = getattr(outer, "primary_color", None) if outer else None
    shoes_color = getattr(shoes, "primary_color", None) if shoes else None
    top_hsv = getattr(top, "primary_color_hsv", None) if top else None
    bottom_hsv = getattr(bottom, "primary_color_hsv", None) if bottom else None
    outer_hsv = getattr(outer, "primary_color_hsv", None) if outer else None
    shoes_hsv = getattr(shoes, "primary_color_hsv", None) if shoes else None
    
    # Check if we have HSV data for all required pieces (top, bottom, shoes)
    # If any critical piece is missing HSV, fall back to rule-based scoring
    has_all_hsv = (
        top_hsv is not None and 
        bottom_hsv is not None and 
        (shoes_hsv is not None if shoes else True)  # shoes optional
    )
    useModel = True  # Enable ML model scoring
    
    # Debug: print HSV availability only if verbose
    if verbose:
        print(f"🔍 HSV Check: top={top_hsv}, bottom={bottom_hsv}, outer={outer_hsv}, shoes={shoes_hsv}")
        print(f"🔍 has_all_hsv={has_all_hsv}, useModel={useModel}")
    
    if has_all_hsv and useModel:
        # Use ML-based scoring with HSV data
        if verbose:
            print("✅ Using ML model for scoring")
        color_score = score_outfit_ml(
            colors=[top_color, bottom_color, outer_color, shoes_color],
            hsvs=[top_hsv, bottom_hsv, outer_hsv, shoes_hsv],
            verbose=verbose
        )
    else:
        # Fall back to rule-based scoring (no HSV data available)
        if verbose:
            print(f"⚠️  Using rule-based scoring (has_all_hsv={has_all_hsv})")
        color_score = score_outfit_colors([top_color, bottom_color, outer_color, shoes_color])
    
    # Apply formality mismatch penalty to color score
    # For each mismatched item, reduce color score by 1.0 (out of 10)
    if formality_mismatch_count > 0:
        original_color_score = color_score
        color_score = max(0.0, color_score - formality_mismatch_count)
        if verbose:
            print(f"⚠️  Formality mismatch penalty: {formality_mismatch_count} items off → Color score: {original_color_score:.1f} - {formality_mismatch_count} = {color_score:.1f}")
    
    score += color_score * 3  # Scale 0-10 to 0-30
    
    return score



def _pick_outfit_legacy(
    tops, bottoms, outers, shoes,
    anchor_top, anchor_bottom, anchor_outer, anchor_shoes,
    season, formality
):
    """
    LEGACY outfit picking logic.
    This is the old algorithm kept as a fallback/placeholder.
    """
    def _want_outer() -> bool:
        """
        Determine if outer layer should be included in outfit:
        - Formal/Semi-formal: ALWAYS need outer (blazer/suit jacket) regardless of season
        - Fall/Winter casual: Need outer for warmth
        - Spring/Summer casual: No outer (too warm)
        """
        # Formal events ALWAYS need a jacket/blazer, even in summer
        if formality in ("semi_formal", "formal"):
            return True
        # For casual/smart-casual, only add outer in cold seasons
        if season in ("winter", "fall"):
            return True
        return False

    # start with anchors if present
    t = anchor_top
    b = anchor_bottom
    o = anchor_outer
    s = anchor_shoes

    best_outfit = None
    best_score = -1
    evaluated_count = 0

    # case 1: anchored top + bottom -> find best compatible outer + shoes
    if t and b:
        print(f"🎯 Case 1: Anchored top+bottom, finding outer+shoes")
        top_outfits = []  # Store all outfits with scores
        
        for o_cand in (outers if _want_outer() else [None]):
            for s_cand in (shoes or [None]):
                if _compatible(t, b, o_cand, s_cand):
                    score = _score_outfit(t, b, o_cand, s_cand, season, formality, verbose=False)
                    evaluated_count += 1
                    
                    outfit_desc = f"Top: {t.category if t else 'None'}, Bottom: {b.category if b else 'None'}, " \
                                  f"Outer: {o_cand.category if o_cand else 'None'}, Shoes: {s_cand.category if s_cand else 'None'}"
                    
                    top_outfits.append({
                        "outfit": {"top": t, "bottom": b, "outer": o_cand, "shoes": s_cand},
                        "score": score,
                        "desc": outfit_desc
                    })
        
        # Sort by score and get top 3
        top_outfits.sort(key=lambda x: x["score"], reverse=True)
        top_3 = top_outfits[:3]
        
        # Print top 3 with detailed ML output
        print(f"\n🏆 Top 3 Outfits (out of {evaluated_count} evaluated):\n")
        for i, item in enumerate(top_3, 1):
            print(f"#{i} - {item['desc']} → Score: {item['score']:.1f}")
            # Re-score with verbose=True to show ML details
            outfit = item["outfit"]
            _score_outfit(outfit["top"], outfit["bottom"], outfit["outer"], outfit["shoes"], 
                         season, formality, verbose=True)
        
        # Select best outfit
        if top_outfits:
            best_outfit = top_3[0]["outfit"]
            best_score = top_3[0]["score"]
        else:
            print(f"   ⚠️ No compatible outfit found, using fallback")
            o = outers[0] if outers and _want_outer() else None
            s = shoes[0] if shoes else None
            best_outfit = {"top": t, "bottom": b, "outer": o, "shoes": s}
        
        return best_outfit

    # case 2: anchored top only -> find best compatible bottom + outer + shoes
    if t and not b:
        print(f"🎯 Case 2: Anchored top, finding bottom+outer+shoes")
        top_outfits = []
        
        for b_cand in bottoms:
            for o_cand in (outers if _want_outer() else [None]):
                for s_cand in (shoes or [None]):
                    if _compatible(t, b_cand, o_cand, s_cand):
                        score = _score_outfit(t, b_cand, o_cand, s_cand, season, formality, verbose=False)
                        evaluated_count += 1
                        
                        outfit_desc = f"Top: {t.category if t else 'None'}, Bottom: {b_cand.category if b_cand else 'None'}, " \
                                      f"Outer: {o_cand.category if o_cand else 'None'}, Shoes: {s_cand.category if s_cand else 'None'}"
                        
                        top_outfits.append({
                            "outfit": {"top": t, "bottom": b_cand, "outer": o_cand, "shoes": s_cand},
                            "score": score,
                            "desc": outfit_desc
                        })
        
        # Sort and get top 3
        top_outfits.sort(key=lambda x: x["score"], reverse=True)
        top_3 = top_outfits[:3]
        
        print(f"\n🏆 Top 3 Outfits (out of {evaluated_count} evaluated):\n")
        for i, item in enumerate(top_3, 1):
            print(f"#{i} - {item['desc']} → Score: {item['score']:.1f}")
            outfit = item["outfit"]
            _score_outfit(outfit["top"], outfit["bottom"], outfit["outer"], outfit["shoes"], 
                         season, formality, verbose=True)
        
        if top_outfits:
            best_outfit = top_3[0]["outfit"]
        else:
            print(f"   ⚠️ No compatible outfit found, using fallback")
            b = bottoms[0] if bottoms else None
            o = outers[0] if outers and _want_outer() else None
            s = shoes[0] if shoes else None
            best_outfit = {"top": t, "bottom": b, "outer": o, "shoes": s}
        
        return best_outfit

    # case 3: anchored bottom only -> find best compatible top + outer + shoes
    if b and not t:
        print(f"🎯 Case 3: Anchored bottom, finding top+outer+shoes")
        top_outfits = []
        
        for t_cand in tops:
            for o_cand in (outers if _want_outer() else [None]):
                for s_cand in (shoes or [None]):
                    if _compatible(t_cand, b, o_cand, s_cand):
                        score = _score_outfit(t_cand, b, o_cand, s_cand, season, formality, verbose=False)
                        evaluated_count += 1
                        
                        outfit_desc = f"Top: {t_cand.category if t_cand else 'None'}, Bottom: {b.category if b else 'None'}, " \
                                      f"Outer: {o_cand.category if o_cand else 'None'}, Shoes: {s_cand.category if s_cand else 'None'}"
                        
                        top_outfits.append({
                            "outfit": {"top": t_cand, "bottom": b, "outer": o_cand, "shoes": s_cand},
                            "score": score,
                            "desc": outfit_desc
                        })
        
        top_outfits.sort(key=lambda x: x["score"], reverse=True)
        top_3 = top_outfits[:3]
        
        print(f"\n🏆 Top 3 Outfits (out of {evaluated_count} evaluated):\n")
        for i, item in enumerate(top_3, 1):
            print(f"#{i} - {item['desc']} → Score: {item['score']:.1f}")
            outfit = item["outfit"]
            _score_outfit(outfit["top"], outfit["bottom"], outfit["outer"], outfit["shoes"], 
                         season, formality, verbose=True)
        
        if top_outfits:
            best_outfit = top_3[0]["outfit"]
        else:
            print(f"   ⚠️ No compatible outfit found, using fallback")
            t = tops[0] if tops else None
            o = outers[0] if outers and _want_outer() else None
            s = shoes[0] if shoes else None
            best_outfit = {"top": t, "bottom": b, "outer": o, "shoes": s}
        
        return best_outfit

    # case 4: no anchors -> find best compatible top + bottom + outer + shoes
    if tops and bottoms:
        print(f"🎯 Case 4: No anchors, finding full outfit")
        top_outfits = []
        
        for t_cand in tops:
            for b_cand in bottoms:
                for o_cand in (outers if _want_outer() else [None]):
                    for s_cand in (shoes or [None]):
                        if _compatible(t_cand, b_cand, o_cand, s_cand):
                            score = _score_outfit(t_cand, b_cand, o_cand, s_cand, season, formality, verbose=False)
                            evaluated_count += 1
                            
                            outfit_desc = f"Top: {t_cand.category if t_cand else 'None'}, Bottom: {b_cand.category if b_cand else 'None'}, " \
                                          f"Outer: {o_cand.category if o_cand else 'None'}, Shoes: {s_cand.category if s_cand else 'None'}"
                            
                            top_outfits.append({
                                "outfit": {"top": t_cand, "bottom": b_cand, "outer": o_cand, "shoes": s_cand},
                                "score": score,
                                "desc": outfit_desc
                            })
        
        top_outfits.sort(key=lambda x: x["score"], reverse=True)
        top_3 = top_outfits[:3]
        
        print(f"\n🏆 Top 3 Outfits (out of {evaluated_count} evaluated):\n")
        for i, item in enumerate(top_3, 1):
            print(f"#{i} - {item['desc']} → Score: {item['score']:.1f}")
            outfit = item["outfit"]
            _score_outfit(outfit["top"], outfit["bottom"], outfit["outer"], outfit["shoes"], 
                         season, formality, verbose=True)
        
        if top_outfits:
            best_outfit = top_3[0]["outfit"]
        else:
            print(f"   ⚠️ No compatible outfit found, using fallback")
            t = tops[0]
            b = bottoms[0]
            o = outers[0] if outers and _want_outer() else None
            s = shoes[0] if shoes else None
            best_outfit = {"top": t, "bottom": b, "outer": o, "shoes": s}
        
        return best_outfit

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

    # Debug logging
    print(f"🔍 Filtered pools for formality='{formality}', season='{season}':")
    print(f"   Tops: {len(tops)} items")
    print(f"   Bottoms: {len(bottoms)} items")
    print(f"   Outers: {len(outers)} items")
    print(f"   Shoes: {len(shoes)} items")
    
    # Log what got filtered out
    for item in all_items:
        if item.outfit_part == "top" and item not in tops and item.id not in anchor_set and item.id not in exclude_set:
            print(f"   ❌ Top filtered: {item.category} (season={item.season}, formality={item.formality})")
        if item.outfit_part == "bottom" and item not in bottoms and item.id not in anchor_set and item.id not in exclude_set:
            print(f"   ❌ Bottom filtered: {item.category} (season={item.season}, formality={item.formality})")

    # add a bit of randomness so repeated "Generate" clicks can explore
    # different valid combinations instead of always picking the same first match
    random.shuffle(tops)
    random.shuffle(bottoms)
    random.shuffle(outers)
    random.shuffle(shoes)

    # ============================================================
    # NEW OUTFIT SELECTION LOGIC (TODO: implement new algorithm)
    # ============================================================
    # TODO: Implement new outfit selection logic here
    # For now, using legacy algorithm as placeholder
    
    outfit = _pick_outfit_legacy(
        tops, bottoms, outers, shoes,
        anchor_top, anchor_bottom, anchor_outer, anchor_shoes,
        season, formality
    )

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
    # print("SUGGESTED OUTFIT:", outfit)

    packed_outfit = {k: _pack(v) for k, v in outfit.items()}

    # Return both weather context and the suggested outfit
    return {
        "weather": weather,       # dict from get_weather(...)
        "outfit": packed_outfit,  # { "top": {...}, "bottom": {...}, ... }
    }




# ---- debug ----
@app.get("/debug/env")
def debug_env():
    return {
        "auto_classify_on_upload": settings.auto_classify_on_upload,
        "has_openai_key": bool(settings.openai_api_key),
    }
