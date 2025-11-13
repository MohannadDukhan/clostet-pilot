import json, re
from typing import Literal, TypedDict
from .enums import Season, OutfitPart, Formality
from .enums import Category
from .config import settings

# choose your provider here (kept minimal; easy to swap)
PROVIDER = "openai"

# enums we’ll accept
Color = Literal[
    "black","white","gray","navy","blue","green","red","yellow","orange","brown","beige","cream","purple","pink","multicolor"
]

class Prediction(TypedDict):
    outfit_part: str
    category: str
    color: str
    season: str
    formality: str

def _normalize(val: str, allowed: list[str], default: str) -> str:
    v = val.strip().lower()
    # common aliases
    alias = {
        "all season":"all-season","allseason":"all-season","semi-formal":"business casual",
        "business-casual":"business casual","sweatshirt":"hoodie","tee":"t_shirt","t-shirt":"t_shirt",
        "denim":"jeans","slacks":"trousers"
    }
    print(v)
    v = alias.get(v, v)
    if v in allowed: return v
    # best-effort contains match
    for a in allowed:
        if v.replace(" ","") == a.replace(" ",""): return a
    return default

def _postprocess(p: dict) -> Prediction:
    print(p)
    cat = _normalize(
        p.get("category", "other"),
        [e.value for e in Category],
        "other",
    )
    outfit_part = _normalize(
        p.get("outfit_part", "other"),
        [e.value for e in OutfitPart] + ["other"],
        "other",
    )
    print(outfit_part)

    col = _normalize(
        p.get("color", "multicolor"),
        [
            "black", "white", "gray", "navy", "blue", "green", "red", "yellow",
            "orange", "brown", "beige", "cream", "purple", "pink", "multicolor",
        ],
        "multicolor",
    )

    # NEW season logic
    raw_season = p.get("season", "all_season")

    # Handle AI returning a list, comma-separated string, or single value
    if isinstance(raw_season, list):
        parts = raw_season
    else:
        parts = [
            s.strip()
            for s in str(raw_season)
            .replace("/", ",")
            .replace("-", "_")
            .split(",")
        ]

    # Normalize each part
    valid = [e.value for e in Season]
    parts = [s for s in parts if s in valid]

    # Reduce to at most 2 seasons
    if len(parts) > 2:
        parts = parts[:2]

    # If 2 parts match a known combo, join them (fall+winter → fall_winter)
    joined = "_".join(parts)
    if joined in valid:
        season = joined
    elif parts:
        season = parts[0]
    else:
        season = "all_season"

    # ----- formality normalization -----
    raw_form = str(p.get("formality", "casual")).lower().strip()

    allowed = [e.value for e in Formality]

    # simple mapping for common synonyms
    if raw_form in allowed:
        formality = raw_form
    elif raw_form in {"sporty", "athletic", "gym", "streetwear"}:
        formality = "casual"
    elif raw_form in {"business_casual"}:
        formality = "smart_casual"
    elif raw_form in {"business", "dressy"}:
        formality = "semi_formal"
    elif "formal" in raw_form:
        formality = "formal"
    else:
        formality = "casual"

    # category-based minimums to fix suits / dress pants / blazers
    cat_lower = (cat or "").lower()
    if any(x in cat_lower for x in ["suit", "dress_pant", "trouser"]):
        # suit pieces and dress pants should never be below semi_formal
        if formality in ["casual", "smart_casual"]:
            formality = "semi_formal"
    if any(x in cat_lower for x in ["blazer", "sport_coat"]):
        if formality in ["casual", "smart_casual"]:
            formality = "semi_formal"

    return {
        "category": cat,
        "outfit_part": outfit_part,
        "color": col,
        "season": season,
        "formality": formality,
    }






def _extract_json(text: str) -> dict:
    # pull the first {...} block; gpt sometimes wraps code fences
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        # relax trailing commas
        s = re.sub(r",\s*([}\]])", r"\1", m.group(0))
        return json.loads(s)

def classify_with_openai(image_path: str) -> Prediction:
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

    prompt = (
        "You are an AI wardrobe assistant analyzing a single clothing photo. "
        "Focus on the main clothing item, ignoring background (bed, floor, other objects). "
        "If the background is cluttered, estimate best you can. "
        "Return STRICT JSON with the keys: category, outfit_part, color, season, formality.\n"
        "Allowed values:\n"
        f"- category: {', '.join([e.value for e in Category])}\n"
        f"- outfit_part: {', '.join([e.value for e in OutfitPart])}, other\n"
        "- color: black, white, gray, navy, blue, green, red, yellow, orange, brown, beige, cream, purple, pink, multicolor\n"
        f"- season: {', '.join([e.value for e in Season])}\n"
        f"- formality: {', '.join([e.value for e in Formality])}\n"
        "SEASON RULES:\n"
        "- Choose ONE OR TWO seasons maximum.\n"
        "- Allowed values: spring, summer, fall, winter, spring_summer, fall_winter, all_season.\n"
        "- Use spring_summer for light warm-weather items (t-shirts, polos, shorts, linen shirts).\n"
        "- Use fall_winter for medium-weight items (hoodies, sweaters, bomber jackets, leather jackets).\n"
        "- Use winter ONLY for thick padded jackets, down jackets, parkas, or visibly insulated coats.\n"
        "- Use fall for light jackets, flannels, cardigans, or light sweaters.\n"
        "- Use all_season for items usable year-round (jeans, chinos, basic t-shirts).\n"
        "FORMALITY RULES:\n"
        "- Allowed values: casual, smart_casual, semi_formal, formal.\n"
        "- Treat gym wear, hoodies, t-shirts, sweatpants, shorts, sneakers as casual.\n"
        "- Treat polos, nice knitwear, chinos, clean sneakers/loafers as smart_casual.\n"
        "- Treat blazers, sport coats, dress shirts, dress pants as at least semi_formal.\n"
        "- Treat full suits, suit jackets with matching dress pants, and ties as formal.\n"
        "Example output: {"
        "\"outfit_part\":\"top\","
        "\"category\":\"sweater\","
        "\"color\":\"navy\","
        "\"season\":\"fall_winter\","
        "\"formality\":\"smart_casual\""
        "}"
        "Do not add commentary or explanations. Output JSON only."
    )

    ...


    with open(image_path, "rb") as f:
        b64 = __import__("base64").b64encode(f.read()).decode("utf-8")

    # gpt-4o is good; mini is cheaper; swap model if you want
    model = "gpt-4o-mini"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role":"user",
                "content": [
                    {"type":"text","text": prompt},
                    {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ],
        temperature=0.0,
    )
    txt = (resp.choices[0].message.content or "").strip()
    print(txt)

    # if the model literally said nothing, retry once with a more forceful instruction
    if not txt:
        force_prompt = (
            prompt
            + "\nIf you cannot detect the item clearly, still return your best guess. "
            "Do NOT leave fields empty."
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": force_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }
            ],
            temperature=0.2,
        )
        txt = (resp.choices[0].message.content or "{}").strip()

    raw = _extract_json(txt)
    if not raw or not isinstance(raw, dict) or "outfit_part" not in raw:
        raw = {
            "outfit_part": "other",
            "color": "multicolor",
            "season": "all_season",
            "formality": "casual",
        }

    return _postprocess(raw)

def classify_image(image_path: str) -> Prediction:
    if PROVIDER == "openai":
        return classify_with_openai(image_path)
    raise RuntimeError("No provider configured")
