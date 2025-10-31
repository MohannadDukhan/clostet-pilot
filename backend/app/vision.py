import json, re
from typing import Literal, TypedDict
from .enums import Season, Gender, OutfitPart, Formality
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
    gender: str

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
        "other"
    )
    outfit_part = _normalize(
        p.get("outfit_part", "other"),
        [e.value for e in OutfitPart] + ["other"],
        "other"
    )
    print(outfit_part)

    col = _normalize(
        p.get("color", "multicolor"),
        ["black", "white", "gray", "navy", "blue", "green", "red", "yellow", "orange", "brown",
         "beige", "cream", "purple", "pink", "multicolor"],
        "multicolor"
    )

    sea = _normalize(
        p.get("season", "all_season"),
        [e.value for e in Season],
        "all_season"
    )

    frm = _normalize(
        p.get("formality", "casual"),
        [e.value for e in Formality],
        "casual"
    )

    gen = p.get("gender", "").strip().lower()
    if gen not in ["male", "female", "unisex", "unknown"]:
        gen = "unknown"

    return {
        "category": cat,
        "outfit_part": outfit_part,
        "color": col,
        "season": sea,
        "formality": frm,
        "gender": gen,
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
    "Return STRICT JSON with the keys: category, outfit_part, color, season, formality, gender.\n"
    "Allowed values:\n"
    f"- category: {', '.join([e.value for e in Category])}\n"
    f"- outfit_part: {', '.join([e.value for e in OutfitPart])}, other\n"
    "- color: black, white, gray, navy, blue, green, red, yellow, orange, brown, beige, cream, purple, pink, multicolor\n"
    f"- season: {', '.join([e.value for e in Season])}\n"
    f"- formality: {', '.join([e.value for e in Formality])}\n"
    "- gender: male, female, unisex, unknown\n"
    "Example output: {"
    "\"outfit_part\":\"top\"," 
    "\"category\":\"sweater\","
    "\"color\":\"navy\"," 
    "\"season\":\"winter\"," 
    "\"formality\":\"casual\"," 
    "\"gender\":\"male\"" 
    "}"
    "Do not add commentary or explanations. Output JSON only."
    )

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
            "gender": "unknown",
        }

    return _postprocess(raw)

def classify_image(image_path: str) -> Prediction:
    if PROVIDER == "openai":
        return classify_with_openai(image_path)
    raise RuntimeError("No provider configured")
