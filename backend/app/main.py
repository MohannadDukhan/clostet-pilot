from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from typing import List
from datetime import date
import requests

from .db import init_db, get_session
from .schemas import UserCreate, UserRead, ItemRead, ItemUpdate, UserUpdate, OutfitCreate, OutfitRead, OutfitUpdate, FeedbackCreate, FeedbackRead, FeedbackUpdate
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

@app.get("/users", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    return crud.list_users(session)

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