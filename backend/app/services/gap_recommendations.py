import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set

from sqlmodel import Session, select

from ..models import Item, OutfitHistory


NEUTRALS = {
    "white",
    "black",
    "gray",
    "grey",
    "beige",
    "tan",
    "navy",
    "cream",
    "ivory",
    "khaki",
}

COLOR_SYNONYMS = {
    "off_white": "white",
    "offwhite": "white",
    "ivory": "white",
    "eggshell": "white",
    "charcoal": "gray",
    "slate": "gray",
    "mid_grey": "gray",
    "mid_gray": "gray",
    "light_grey": "gray",
    "light_gray": "gray",
    "dark_grey": "gray",
    "dark_gray": "gray",
    "navy": "blue",
    "midnight_blue": "blue",
    "cobalt": "blue",
    "sky_blue": "blue",
    "light_blue": "blue",
    "dark_blue": "blue",
}

FORMALITY_SYNONYMS = {
    "smartcasual": "smart_casual",
    "smart_casual": "smart_casual",
    "smart casual": "smart_casual",
    "semi_formal": "formal",
    "semiformal": "formal",
    "semi formal": "formal",
    "business casual": "business_casual",
    "business_casual": "business_casual",
    "sport": "sporty",
    "athletic": "sporty",
}

FORMALITY_COMPAT = {
    "casual": {"casual", "smart_casual", "sporty"},
    "sporty": {"sporty", "casual"},
    "smart_casual": {"casual", "smart_casual", "business_casual", "formal"},
    "business_casual": {"business_casual", "smart_casual", "formal"},
    "formal": {"formal", "business_casual", "smart_casual"},
}

CASUAL_BAND = {"casual", "smart_casual", "sporty"}
FORMAL_BAND = {"smart_casual", "formal", "business_casual"}

FALLBACK_REASON_TEXT = {
    "white_sneakers": "Improves shoe versatility for casual outfits.",
    "black_sneakers": "Adds a flexible dark shoe option for repeat use.",
    "midweight_jacket": "Adds practical outerwear coverage for shifting temperatures.",
    "plain_white_tee": "Adds a neutral top anchor for easier pairing.",
    "dark_jeans": "Strengthens everyday bottom coverage with a versatile staple.",
    "neutral_hoodie": "Adds a casual layering piece for cooler days.",
}



def _norm(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")



def normalize_color(value: Optional[str]) -> str:
    raw = _norm(value)
    if not raw:
        return ""
    return COLOR_SYNONYMS.get(raw, raw)



def _is_neutral_color(value: Optional[str]) -> bool:
    raw = _norm(value)
    canonical = normalize_color(value)
    return raw in NEUTRALS or canonical in NEUTRALS



def normalize_season(value: Optional[str]) -> Set[str]:
    raw = _norm(value)
    if not raw or raw in {"unknown", "none", "null"}:
        return set()
    if raw in {"all", "all_season", "any"}:
        return {"all"}
    if raw in {"fall_winter", "winter_fall"}:
        return {"fall", "winter"}
    if raw in {"spring_summer", "summer_spring"}:
        return {"spring", "summer"}
    if raw in {"spring", "summer", "fall", "winter"}:
        return {raw}

    tokens = {p for p in raw.split("_") if p in {"spring", "summer", "fall", "winter"}}
    return tokens



def normalize_formality(value: Optional[str]) -> str:
    raw = _norm(value)
    if not raw or raw in {"unknown", "none", "null", "any"}:
        return ""
    raw = FORMALITY_SYNONYMS.get(raw, raw)
    return raw if raw in {"casual", "smart_casual", "business_casual", "formal", "sporty"} else ""



def _normalize_category(value: Optional[str]) -> str:
    return _norm(value)



def _season_compatible(item_season: Optional[str], template_seasons: List[str]) -> bool:
    template_set: Set[str] = set()
    for season in template_seasons or []:
        template_set |= normalize_season(season)

    if not template_set or "all" in template_set:
        return True

    item_set = normalize_season(item_season)
    if not item_set:
        return True
    if "all" in item_set:
        return True
    return bool(item_set & template_set)



def _formality_compatible(item_formality: Optional[str], template_formality: List[str]) -> bool:
    template_set = {normalize_formality(v) for v in (template_formality or [])}
    template_set.discard("")

    if not template_set:
        return True

    item_norm = normalize_formality(item_formality)
    if not item_norm:
        return True

    if item_norm in template_set:
        return True

    compat_set = FORMALITY_COMPAT.get(item_norm, {item_norm})
    return bool(compat_set & template_set)



def _color_compatible(item_color: Optional[str], template_colors: List[str]) -> bool:
    if not template_colors:
        return True

    item_raw = _norm(item_color)
    item_norm = normalize_color(item_color)

    if not item_norm and not item_raw:
        return True

    template_set = {normalize_color(v) for v in template_colors}
    raw_template = {_norm(v) for v in template_colors}

    if "neutral" in raw_template and _is_neutral_color(item_color):
        return True

    if item_norm in template_set:
        return True

    # If item color is neutral and template asks for a specific neutral name.
    return _is_neutral_color(item_color) and bool(template_set & {"white", "black", "gray", "beige", "tan"})



def _supports_band(template_formality: List[str], band: str) -> bool:
    normalized = {normalize_formality(v) for v in (template_formality or [])}
    normalized.discard("")
    if not normalized:
        return True
    if band == "formal_band":
        return bool(normalized & FORMAL_BAND)
    return bool(normalized & CASUAL_BAND)



def _supports_formal_or_smart(template_formality: List[str]) -> bool:
    normalized = {normalize_formality(v) for v in (template_formality or [])}
    return bool(normalized & {"smart_casual", "business_casual", "formal"})



def _cold_from_history(row: OutfitHistory) -> bool:
    if row.weather_temp_c is not None and row.weather_temp_c <= 8:
        return True
    return "winter" in normalize_season(row.inferred_season) or "fall" in normalize_season(row.inferred_season)



@lru_cache(maxsize=1)
def load_templates() -> List[Dict]:
    data_path = Path(__file__).resolve().parents[2] / "data" / "wardrobe_templates.json"
    with data_path.open("r", encoding="utf-8") as f:
        return json.load(f)



def matches_template(item: Item, template: Dict) -> bool:
    if _norm(getattr(item, "outfit_part", None)) != _norm(template.get("outfit_part")):
        return False

    categories = {_normalize_category(c) for c in template.get("categories", []) if _normalize_category(c)}
    item_category = _normalize_category(getattr(item, "category", None))
    if categories and item_category and item_category not in categories:
        return False

    if not _color_compatible(getattr(item, "primary_color", None), template.get("colors", []) or []):
        return False

    if not _season_compatible(getattr(item, "season", None), template.get("seasons", []) or []):
        return False

    if not _formality_compatible(getattr(item, "formality", None), template.get("formality", []) or []):
        return False

    return True



def _template_match_count(wardrobe: List[Item], template: Dict) -> int:
    return sum(1 for item in wardrobe if matches_template(item, template))



def compute_gap_recommendations(session: Session, user_id: int, limit: int = 3) -> List[Dict]:
    target_limit = max(1, min(limit, 6))
    min_needed = 3 if target_limit >= 3 else target_limit

    templates = load_templates()
    templates_by_id = {str(t.get("id")): t for t in templates}

    wardrobe = session.exec(select(Item).where(Item.user_id == user_id)).all()
    history = session.exec(
        select(OutfitHistory)
        .where(OutfitHistory.user_id == user_id)
        .order_by(OutfitHistory.created_at.desc())
        .limit(50)
    ).all()

    slot_counts = Counter(_norm(getattr(item, "outfit_part", None)) for item in wardrobe)
    has_neutral_top = any(
        _norm(getattr(item, "outfit_part", None)) == "top" and _is_neutral_color(getattr(item, "primary_color", None))
        for item in wardrobe
    )

    usage = {"shoes": Counter(), "outerwear": Counter()}
    usage_total = {"shoes": 0, "outerwear": 0}

    formality_counter = Counter()
    cold_count = 0
    rain_count = 0

    for row in history:
        if row.shoes_item_id:
            usage["shoes"][row.shoes_item_id] += 1
            usage_total["shoes"] += 1
        if row.outerwear_item_id:
            usage["outerwear"][row.outerwear_item_id] += 1
            usage_total["outerwear"] += 1

        formality_counter[normalize_formality(row.requested_formality)] += 1
        if _cold_from_history(row):
            cold_count += 1
        if "rain" in _norm(row.weather_condition):
            rain_count += 1

    total_history = len(history)
    cold_freq = (cold_count / total_history) if total_history else 0.0
    rain_freq = (rain_count / total_history) if total_history else 0.0

    formalish = (
        formality_counter.get("smart_casual", 0)
        + formality_counter.get("business_casual", 0)
        + formality_counter.get("formal", 0)
    )
    formal_freq = (formalish / total_history) if total_history else 0.0

    dominant_formality_values = [key for key, _ in formality_counter.most_common(2) if key]
    if any(v in FORMAL_BAND for v in dominant_formality_values):
        dominant_band = "formal_band"
    else:
        dominant_band = "casual_band"

    top_share_by_slot = {}
    for slot in ("shoes", "outerwear"):
        total = usage_total[slot]
        if total and usage[slot]:
            top_share_by_slot[slot] = max(usage[slot].values()) / total
        else:
            top_share_by_slot[slot] = 0.0

    strict_recs: List[Dict] = []

    for template in templates:
        template_id = str(template.get("id"))
        part = _norm(template.get("outfit_part"))
        template_formality = template.get("formality", []) or []

        match_count = _template_match_count(wardrobe, template)
        if match_count == 0:
            missing_score = 1.0
        elif match_count == 1:
            missing_score = 0.4
        else:
            missing_score = 0.0

        if missing_score <= 0.0:
            continue

        diversity_pressure_score = 0.0
        if part in {"shoes", "outerwear"} and _supports_band(template_formality, dominant_band):
            top_share = top_share_by_slot.get(part, 0.0)
            if top_share > 0.75:
                diversity_pressure_score = 0.8
            elif top_share > 0.6:
                diversity_pressure_score = 0.5

        weather_relevance_score = 0.0
        if part == "outerwear" and cold_freq >= 0.4:
            weather_relevance_score += 0.4

        category_tokens = {_norm(v) for v in (template.get("categories") or [])}
        if template_id == "rain_jacket" or "rain_jacket" in category_tokens:
            if rain_freq > 0:
                weather_relevance_score += 0.4

        formality_relevance_score = 0.0
        if formal_freq >= 0.35 and _supports_formal_or_smart(template_formality):
            formality_relevance_score = 0.2

        total_score = (
            0.55 * missing_score
            + 0.25 * diversity_pressure_score
            + 0.15 * weather_relevance_score
            + 0.05 * formality_relevance_score
        )

        if total_score < 0.35:
            continue

        reasons: List[str] = []
        if missing_score >= 0.9:
            reasons.append("MISSING_TEMPLATE")
        if part == "shoes" and top_share_by_slot.get("shoes", 0.0) > 0.6:
            reasons.append("LOW_DIVERSITY_SHOES")
        if part == "outerwear" and cold_freq >= 0.4:
            reasons.append("COLD_WEATHER_OUTERWEAR")
        if formal_freq >= 0.35 and _supports_formal_or_smart(template_formality):
            reasons.append("FORMAL_COVERAGE")

        strict_recs.append(
            {
                "templateId": template_id,
                "name": template.get("name"),
                "outfitPart": part,
                "score": round(total_score, 2),
                "reasons": reasons,
                "summary": template.get("description") or f"Improves {part} coverage with a versatile staple.",
            }
        )

    strict_recs.sort(key=lambda row: (-row["score"], row["templateId"]))

    selected: List[Dict] = []
    selected_ids: Set[str] = set()

    def add_recommendation(template_id: str, reason_code: str, force: bool = False) -> None:
        nonlocal selected
        if len(selected) >= target_limit:
            return
        if template_id in selected_ids:
            return

        template = templates_by_id.get(template_id)
        if not template:
            return

        match_count = _template_match_count(wardrobe, template)
        if not force and match_count >= 2:
            return

        score = 0.78 if match_count == 0 else 0.46
        selected.append(
            {
                "templateId": template_id,
                "name": template.get("name"),
                "outfitPart": _norm(template.get("outfit_part")),
                "score": round(score, 2),
                "reasons": [reason_code],
                "summary": template.get("description") or FALLBACK_REASON_TEXT.get(
                    template_id,
                    "Improves wardrobe coverage for everyday outfit generation.",
                ),
            }
        )
        selected_ids.add(template_id)

    # Add strict recommendations first.
    for rec in strict_recs:
        if len(selected) >= target_limit:
            break
        selected.append(rec)
        selected_ids.add(rec["templateId"])

    fallback_candidates: List[tuple[str, str]] = []

    if slot_counts.get("shoes", 0) < 2:
        fallback_candidates.append(("white_sneakers", "MISSING_STAPLE_SHOES"))
        fallback_candidates.append(("black_sneakers", "MISSING_STAPLE_SHOES"))
    if slot_counts.get("outerwear", 0) == 0:
        fallback_candidates.append(("midweight_jacket", "MISSING_STAPLE_OUTERWEAR"))
    if not has_neutral_top:
        fallback_candidates.append(("plain_white_tee", "MISSING_STAPLE_TOP"))

    # Ensure we can reach 3 when possible.
    fallback_candidates.extend(
        [
            ("dark_jeans", "MISSING_STAPLE_BOTTOM"),
            ("neutral_hoodie", "MISSING_STAPLE_TOP"),
            ("midweight_jacket", "MISSING_STAPLE_OUTERWEAR"),
            ("white_sneakers", "MISSING_STAPLE_SHOES"),
            ("button_down_white", "FORMAL_COVERAGE"),
        ]
    )

    for template_id, reason_code in fallback_candidates:
        if len(selected) >= target_limit and len(selected) >= min_needed:
            break
        add_recommendation(template_id, reason_code)

    return selected[:target_limit]
