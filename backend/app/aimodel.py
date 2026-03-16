import csv
from pathlib import Path
import pickle


# Try to load trained model (if exists)
MODEL_PATH = Path(__file__).parent.parent / "color_model.pkl"
try:
    with open(MODEL_PATH, 'rb') as f:
        trained_model = pickle.load(f)
    print(f"✅ Loaded trained model from {MODEL_PATH}")
except FileNotFoundError:
    trained_model = None
    print(f"⚠️  No trained model found at {MODEL_PATH}. Will use placeholder scoring.")


def hue_distance(h1: float, h2: float) -> float:
    """Calculate circular distance between two hues on color wheel (0-360)."""
    d = abs(h1 - h2)
    return min(d, 360 - d)


def extract_features(hsvs: list[str]) -> list[float]:
    """
    Extract 6 core color harmony features from HSV values.

    Features (in order):
        avg_hue_distance  – average circular hue distance across all garment pairs
        max_hue_distance  – worst (most clashing) pair distance
        avg_saturation    – mean saturation of all garments
        high_sat_count    – number of garments with saturation ≥ 60 (loud pieces)
        neutral_count     – number of garments with saturation < 20 (neutral anchors)
        has_contrast      – 1 if outfit has both a light (V>70) and dark (V<30) piece

    Args:
        hsvs: List of HSV strings [top, bottom, outer, shoes]

    Returns:
        List of 6 numeric features for ML model
    """
    # Parse HSVs
    parsed_hsvs = []
    for hsv_str in hsvs:
        if hsv_str:
            try:
                parts = hsv_str.split(",")
                h = float(parts[0])
                s = float(parts[1])
                v = float(parts[2])
                parsed_hsvs.append((h, s, v))
            except (ValueError, IndexError):
                parsed_hsvs.append(None)
        else:
            parsed_hsvs.append(None)

    top_hsv    = parsed_hsvs[0]
    bottom_hsv = parsed_hsvs[1]
    outer_hsv  = parsed_hsvs[2]
    shoes_hsv  = parsed_hsvs[3]

    # Neutral fallback (black) used when a piece has no HSV data
    NEUTRAL = (0.0, 0.0, 0.0)
    top_safe    = top_hsv    or NEUTRAL
    bottom_safe = bottom_hsv or NEUTRAL
    shoes_safe  = shoes_hsv  or NEUTRAL

    # ── Hue distances across every garment pair ────────────────────────────
    all_distances = [
        hue_distance(top_safe[0], bottom_safe[0]),
        hue_distance(top_safe[0], shoes_safe[0]),
        hue_distance(bottom_safe[0], shoes_safe[0]),
    ]
    if outer_hsv:
        all_distances += [
            hue_distance(top_safe[0],    outer_hsv[0]),
            hue_distance(bottom_safe[0], outer_hsv[0]),
            hue_distance(shoes_safe[0],  outer_hsv[0]),
        ]

    avg_hue_distance = sum(all_distances) / len(all_distances)
    max_hue_distance = max(all_distances)

    # ── Saturation features ────────────────────────────────────────────────
    # Use all non-None HSVs for saturation/brightness (outer may be absent)
    present_hsvs = [hsv for hsv in parsed_hsvs if hsv is not None]
    # Always include top+bottom+shoes via their safe fallbacks so missing items
    # don't silently shrink the pool (use parsed_hsvs[0..3] safe versions)
    scored_hsvs = [top_safe, bottom_safe, shoes_safe] + ([outer_hsv] if outer_hsv else [])
    saturations = [hsv[1] for hsv in scored_hsvs]
    avg_saturation = sum(saturations) / len(saturations)
    high_sat_count = sum(1 for s in saturations if s >= 60)
    neutral_count  = sum(1 for s in saturations if s < 20)

    # ── Brightness contrast ────────────────────────────────────────────────
    values    = [hsv[2] for hsv in scored_hsvs]
    has_light = any(v > 70 for v in values)
    has_dark  = any(v < 30 for v in values)
    has_contrast = 1 if (has_light and has_dark) else 0

    # Return all 6 features in consistent order
    return [
        avg_hue_distance,
        max_hue_distance,
        avg_saturation,
        high_sat_count,
        neutral_count,
        has_contrast,
    ]


def score_outfit_ml(colors: list[str], hsvs: list[str], verbose: bool = True) -> float:
    """Score an outfit using ML model based on color harmony features."""
    features = extract_features(hsvs)
    
    # Use trained model if available, otherwise return placeholder
    if trained_model is not None:
        import warnings
        # Suppress the feature names warning since we're passing features in correct order
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="X does not have valid feature names")
            score = trained_model.predict([features])[0]  # Model returns array, get first element
        score = round(max(0.0, min(score, 10.0)), 1)  # Clamp to 0-10 range
        
        # Print detailed prediction info only if verbose
        if verbose:
            print("\n" + "="*60)
            print(" ML MODEL PREDICTION")
            print("="*60)
            print(f"Input Colors: {colors}")
            print(f"Input HSVs:   {hsvs}")
            print(f"\nExtracted Features (6 total):")
            print(f"  • avg_hue_distance : {features[0]:.1f}°")
            print(f"  • max_hue_distance : {features[1]:.1f}°")
            print(f"  • avg_saturation   : {features[2]:.1f}")
            print(f"  • high_sat_count   : {int(features[3])}  (pieces with S≥60)")
            print(f"  • neutral_count    : {int(features[4])}  (pieces with S<20)")
            print(f"  • has_contrast     : {int(features[5])}  (light+dark pair present)")
            print(f"\n FINAL SCORE: {score}/10")
            print("="*60 + "\n")
        
        return score
    else:
        if verbose:
            print("⚠️  No model loaded, returning placeholder score")
        return 5.0  # Neutral score until model is trained


# Global list to collect training examples in memory
_training_batch = []


def save_training_data(hsvs: list[str], rating: float):
    """
    Add outfit features + manual rating to batch (in memory).
    Call write_training_data() to save all at once to CSV.
    
    Usage:
        save_training_data(
            hsvs=["210,100,25", "0,0,100", None, "0,0,0"],
            rating=8.5
        )
        # ... add more examples ...
        write_training_data()  # Save all to CSV
    
    Args:
        hsvs: List of HSV strings [top, bottom, outer, shoes]
        rating: Your manual score (0-10) for the outfit
    """
    # Extract features using shared function
    features = extract_features(hsvs)
    
    # Add to batch (not written to file yet)
    _training_batch.append(features + [rating])
    print(f"✅ Added training example with rating {rating} (batch size: {len(_training_batch)})")


def write_training_data():
    """
    Write all collected training examples to a NEW CSV file.
    Overwrites existing training_data.csv.
    """
    csv_file = Path(__file__).parent.parent / "training_data.csv"
    
    if not _training_batch:
        print("⚠️  No training examples to save!")
        return
    
    # Write to file (overwrite mode 'w')
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        header = [
            'avg_hue_distance',
            'max_hue_distance',
            'avg_saturation',
            'high_sat_count',
            'neutral_count',
            'has_contrast',
            'rating'
        ]
        writer.writerow(header)
        
        # Write all rows
        writer.writerows(_training_batch)
    
    print(f"\n✅ Saved {len(_training_batch)} training examples to {csv_file}")
    print(f"   File overwritten with new data only!")
    
    # Clear batch
    _training_batch.clear()


def add(outfit_hsvs, rating):
    save_training_data(
        hsvs=outfit_hsvs,
        rating=rating
    )


def generate_training_data():
    # ─────────────────────────────────────────────────────────────
    #  TIER 1 — EXCELLENT  (9.0 – 9.8)
    #  Harmonic hues, low-to-moderate saturation, clear contrast
    # ─────────────────────────────────────────────────────────────
    add(["210,40,25", "0,0,90", "30,25,40", "0,0,10"], 9.7)   # navy + white + tan jacket + black shoes
    add(["0,0,15", "0,0,85", "210,35,35", "0,0,10"], 9.5)     # black + off-white + muted blue coat
    add(["25,30,60", "30,25,55", None, "0,0,10"], 9.4)         # camel tee + tan chinos + black shoes
    add(["220,45,30", "215,40,28", None, "30,20,25"], 9.3)     # two navy tones + brown shoes (monochrome)
    add(["160,25,40", "0,0,15", "0,0,80", "160,15,20"], 9.2)   # sage + black + light gray coat + olive shoes
    add(["10,35,30", "210,25,20", "0,0,90", "0,0,10"], 9.1)    # muted rust + muted navy + white coat
    add(["200,40,40", "30,20,70", None, "0,0,10"], 9.0)        # steel blue + cream + black shoes
    add(["45,15,85", "0,0,10", "210,40,30", "0,0,95"], 9.5)    # cream top + black pants + navy jacket + white shoes
    add(["30,35,55", "210,30,30", "0,0,95", "0,0,10"], 9.2)    # camel + navy + off-white coat
    add(["120,20,40", "100,15,35", "0,0,90", "0,0,10"], 8.9)   # two olives + white coat (analogous)

    # ─────────────────────────────────────────────────────────────
    #  TIER 2 — GOOD  (7.0 – 8.8)
    #  Mostly harmonic, one accent ok, balanced saturation
    # ─────────────────────────────────────────────────────────────
    add(["0,65,50", "210,45,35", "0,0,85", "0,0,10"], 8.5)    # muted red + navy + white coat
    add(["0,0,10", "0,0,90", "0,70,50", "0,0,20"], 8.6)       # black + white + red accent coat (classic contrast)
    add(["260,45,40", "30,35,55", "0,0,90", "0,0,10"], 7.8)   # soft purple + tan + white
    add(["210,55,45", "180,45,40", "0,0,90", "0,0,10"], 8.0)   # blue + teal + white (analogous)
    add(["300,40,45", "210,35,30", "0,0,90", "0,0,10"], 7.5)   # dusty pink + navy + white
    add(["30,65,65", "0,0,15", "0,0,90", "0,0,10"], 7.2)      # bold orange + black pants + white coat
    add(["90,35,50", "210,30,30", "0,0,80", "0,0,15"], 7.9)   # sage-yellow + navy + light gray
    add(["20,50,55", "40,40,50", "0,0,90", "0,0,10"], 7.6)    # warm earth + light tan + white
    add(["200,50,45", "20,45,50", "0,0,90", "0,0,10"], 7.3)   # blue + warm orange (complement) + white
    add(["210,70,45", "30,60,50", "0,0,80", "0,0,0"], 7.7)    # blue + orange + light gray + black shoes
    add(["0,60,50", "180,55,45", "0,0,70", "0,0,10"], 7.4)    # red + teal (complement) + gray
    add(["120,50,45", "300,50,45", "0,0,40", "0,0,0"], 7.1)   # green + magenta (complement) + charcoal
    add(["60,50,50", "240,50,45", "0,0,30", "0,0,0"], 7.0)    # yellow + purple (complement) + dark gray
    add(["0,0,90", "210,75,30", "30,55,50", "0,0,0"], 7.8)    # white + navy + camel (triadic-ish)
    add(["350,55,45", "345,50,40", "355,60,50", "0,65,45"], 3.5)  # all red everything — looks like a costume
    add(["220,50,30", "230,45,25", "215,55,35", "210,45,25"], 3.8) # all blue everything — too matchy
    add(["50,35,60", "55,30,55", "45,40,65", None], 7.8)      # earthy yellow analogous trio (low sat, close hues = fine)
    add(["0,0,20", "0,0,50", "0,0,75", None], 7.8)            # grayscale gradient — classic and clean
    add(["0,0,70", "30,10,30", "0,0,0", None], 7.6)           # gray + hint brown + black
    add(["250,15,30", "0,0,80", "0,0,50", None], 7.8)         # muted blue + white + gray

    # ─────────────────────────────────────────────────────────────
    #  TIER 3 — MEDIOCRE  (4.5 – 6.5)
    #  One clear fault: slightly loud, slightly off-hue, or flat
    # ─────────────────────────────────────────────────────────────
    add(["0,55,55", "210,50,45", None, "0,0,0"], 6.1)          # red + blue (ok but no anchor)
    add(["120,50,50", "30,45,50", None, "0,0,0"], 5.9)         # green + brown (acceptable)
    add(["240,50,50", "60,50,55", None, "0,0,0"], 5.6)         # blue + yellow (muted clash)
    add(["30,60,60", "210,55,50", None, "0,0,0"], 5.8)         # orange + blue (border loud)
    add(["280,50,55", "120,45,45", None, "0,0,0"], 5.5)        # purple + green (muted clash)
    add(["60,55,55", "240,55,50", None, "0,0,0"], 5.7)         # yellow + purple
    add(["180,45,50", "30,45,50", None, "0,0,0"], 5.4)         # teal + orange
    add(["0,0,60", "0,0,50", "0,0,40", "0,0,30"], 7.5)        # all grays with variety — clean, wearable
    add(["30,10,70", "40,10,65", "0,0,80", "0,0,20"], 7.2)     # near-neutral beiges + B&W — polished earthy
    add(["200,10,60", "210,10,55", "0,0,75", "0,0,25"], 7.0)   # washed-out blues + neutrals — subtle
    add(["210,80,30", "0,0,80", "120,75,50", "0,0,0"], 5.0)    # navy+white ok but green jacket clashes
    add(["30,70,60", "0,0,60", "300,70,55", "0,0,0"], 4.6)     # orange + gray + loud pink jacket
    add(["340,40,50", "160,40,50", None, "0,0,0"], 5.2)        # dusty rose + sage (ok muted complement)
    add(["0,0,50", "0,0,70", "210,30,40", "0,0,0"], 6.5)      # two grays + muted blue (safe)
    add(["30,50,70", "210,40,60", "0,0,80", None], 6.3)        # light orange + muted blue + white

    # ─────────────────────────────────────────────────────────────
    #  TIER 4 — BAD  (2.5 – 4.2)
    #  Clearly loud OR clearly clashing hues
    # ─────────────────────────────────────────────────────────────
    add(["0,90,60", "120,90,60", "60,90,60", "300,90,60"], 2.5)  # red+green+yellow+magenta ALL saturated
    add(["30,80,70", "200,80,70", "150,80,70", "280,80,70"], 3.0) # four clashing loud pieces
    add(["10,85,75", "180,85,75", "260,85,75", "90,85,75"], 2.8)  # red-orange+teal+blue+lime all loud
    add(["300,95,65", "60,95,65", "180,95,65", "120,95,65"], 2.6) # magenta+yellow+teal+green max loud
    add(["0,100,60", "120,100,60", None, "300,100,60"], 2.4)     # red+green+magenta (Christmas disaster)
    add(["60,100,60", "240,100,60", None, "0,100,60"], 2.5)      # yellow+purple+red full sat
    add(["120,90,50", "30,90,50", None, "240,90,50"], 3.0)       # green+orange+blue all vivid
    add(["240,90,50", "0,0,40", "30,90,70", "0,0,0"], 4.0)      # blue + dark neutral + LOUD orange jacket
    add(["0,100,60", "0,0,90", "60,100,60", "0,0,0"], 3.5)      # bright red + white + bright yellow jacket
    add(["20,100,70", "0,0,90", "200,100,70", "0,0,0"], 3.2)    # saturated orange + white + saturated blue coat

    # ─────────────────────────────────────────────────────────────
    #  TIER 5 — TERRIBLE  (1.0 – 2.4)
    #  Both clashing AND loud simultaneously
    # ─────────────────────────────────────────────────────────────
    add(["0,100,65", "240,100,65", None, "120,100,65"], 1.9)     # red+blue+green max sat
    add(["300,100,60", "60,100,60", None, "240,100,60"], 2.1)    # magenta+yellow+blue max sat
    add(["0,100,70", "180,100,70", None, "90,100,70"], 1.8)      # red+teal+lime full blast
    add(["210,100,60", "30,100,60", None, "150,100,60"], 1.7)    # blue+orange+green-blue all 100%
    add(["10,100,70", "130,100,70", "250,100,70", "0,0,0"], 1.5) # three full-sat clashing + black shoes
    add(["0,100,80", "180,100,80", "90,100,80", "0,0,0"], 1.0)   # bright red+teal+lime (worst)
    add(["70,100,80", "190,100,80", "310,100,80", "0,0,0"], 1.2) # three neon clashing pastels
    add(["10,100,30", "130,100,30", "250,100,30", "0,0,0"], 1.4) # three dark ultra-saturated clashes
    add(["0,95,60", "120,95,60", "240,95,60", "60,95,60"], 2.0)  # four-way loud clash
    add(["45,95,80", "210,95,80", "0,95,80", "120,95,80"], 1.6)  # four neon nightmare

    # ─────────────────────────────────────────────────────────────
    #  BONUS — OUTERWEAR COMBOS (good layering vs bad layering)
    # ─────────────────────────────────────────────────────────────
    add(["210,70,30", "0,0,80", "30,40,40", "0,0,0"], 7.8)     # navy + white + tan jacket (classic)
    add(["0,0,90", "210,40,30", "30,25,20", "0,0,0"], 8.1)     # white + muted blue + dark tan jacket
    add(["30,55,50", "0,0,70", "120,25,30", "0,0,0"], 7.6)     # camel + gray + olive coat
    add(["0,65,55", "0,0,50", "0,0,25", "0,0,0"], 7.9)         # red top + gray pants + dark coat
    add(["180,45,40", "0,0,80", "270,25,35", "0,0,0"], 7.5)    # teal + white + muted violet coat
    add(["100,85,50", "0,0,30", "280,85,50", "0,0,0"], 3.4)    # lime green + dark + bright purple coat

    # ─────────────────────────────────────────────────────────────
    #  BONUS — BLACK & WHITE ANCHORS
    # ─────────────────────────────────────────────────────────────
    add(["0,0,0", "0,0,100", "210,65,40", "0,0,0"], 7.8)       # B+W + blue coat + black shoes
    add(["0,0,0", "0,0,100", "0,65,50", "0,0,0"], 7.0)         # B+W + red coat
    add(["0,0,0", "210,65,40", "30,55,50", "0,0,0"], 6.8)      # black + blue + orange (ok, complementary)
    add(["0,0,100", "120,75,50", "300,75,50", "0,0,100"], 5.0)  # white + green + magenta + white shoes (loud)

    # ─────────────────────────────────────────────────────────────
    #  BONUS — EDGE CASES (model needs tricky ones)
    # ─────────────────────────────────────────────────────────────
    add(["210,40,30", "220,35,35", "120,90,60", "0,0,10"], 6.0)  # nice base but one loud outlier
    add(["0,0,10", "0,0,90", "0,75,50", "120,20,40"], 8.0)      # B+W contrast + red + muted olive shoe
    add(["30,30,50", "210,30,30", "0,0,90", "300,55,50"], 7.2)   # earth + navy + white + loud magenta shoe
    add(["180,40,40", "200,45,45", "0,0,85", "30,80,70"], 6.8)   # teal + blue + white + loud orange shoe
    add(["60,20,80", "240,50,50", "0,0,90", "0,0,10"], 7.0)     # cream + medium blue + white (ok)

    # ─────────────────────────────────────────────────────────────
    #  EXTRA TIER 1 — MORE EXCELLENT  (8.8 – 9.6)
    # ─────────────────────────────────────────────────────────────
    add(["0,0,10", "210,35,30", "0,0,85", "30,15,20"], 9.6)    # black + navy + off-white coat + brown shoes
    add(["30,25,65", "25,20,55", "0,0,10", "0,0,10"], 9.3)     # two warm tans + black jacket + black shoes
    add(["210,30,25", "200,25,30", "0,0,90", "0,0,5"], 9.1)    # two dark blues + white coat (tonal)
    add(["0,0,85", "0,0,25", "30,30,45", "0,0,10"], 9.4)       # white + charcoal + camel coat + black shoes
    add(["180,20,35", "170,15,30", None, "0,0,10"], 8.8)        # two muted teals + black shoes (subtle)
    add(["350,25,40", "0,0,80", "210,30,25", "0,0,10"], 9.0)   # dusty rose + off-white + navy coat
    add(["40,30,70", "0,0,10", None, "30,20,30"], 7.2)          # light tan + black pants + brown shoes

    # ─────────────────────────────────────────────────────────────
    #  EXTRA TIER 2 — MORE GOOD  (7.0 – 8.8)
    # ─────────────────────────────────────────────────────────────
    add(["0,55,45", "0,0,10", "0,0,85", "0,0,10"], 8.3)        # muted red + black + white coat (classic)
    add(["270,40,35", "0,0,80", "0,0,10", "0,0,10"], 7.6)      # muted purple + off-white + black coat
    add(["150,45,40", "30,30,50", "0,0,90", "0,0,10"], 8.8)    # forest green + tan + white coat
    add(["30,50,55", "0,0,10", "210,50,35", "0,0,10"], 7.4)    # camel + black + blue coat
    add(["0,45,40", "210,40,30", None, "0,0,10"], 7.9)          # brick red + navy (classic pair)
    add(["330,35,45", "0,0,75", None, "30,20,25"], 7.5)         # mauve + light gray + brown shoes
    add(["180,50,40", "30,40,50", "0,0,10", "0,0,10"], 7.3)    # teal + tan + black coat (complement)
    add(["60,40,55", "0,0,20", "0,0,80", "0,0,10"], 8.5)       # muted gold + dark gray + light gray coat
    add(["210,50,40", "0,0,80", "0,55,45", "0,0,10"], 8.0)     # blue + off-white + red coat (tricolor)
    add(["120,35,40", "0,0,10", "30,25,35", "0,0,10"], 7.7)    # olive + black + tan coat

    # ─────────────────────────────────────────────────────────────
    #  EXTRA TIER 3 — MORE MEDIOCRE  (4.5 – 6.5)
    #  Biggest gap in original data — model needs these most
    # ─────────────────────────────────────────────────────────────
    add(["0,60,55", "120,55,45", None, "0,0,0"], 5.3)          # red + green (muted but still clashing)
    add(["240,60,50", "30,60,55", None, "0,0,0"], 5.7)         # blue + orange (both medium sat)
    add(["0,0,45", "0,0,55", "0,0,65", "0,0,35"], 7.0)         # four grays with spread — understated but works
    add(["300,55,50", "60,55,50", None, "0,0,0"], 5.1)         # pink + yellow (odd pair)
    add(["150,50,45", "330,50,50", None, "0,0,0"], 5.4)        # green-cyan + rose (split complement)
    add(["210,65,40", "0,0,70", "30,65,55", "0,0,0"], 6.2)     # blue + gray + orange coat (ok but busy)
    add(["0,50,50", "0,0,60", "120,50,45", "0,0,0"], 5.6)      # red + gray + green coat (clash softened by gray)
    add(["45,55,65", "225,50,50", None, "0,0,0"], 5.8)         # warm yellow + steel blue (moderate)
    add(["270,55,50", "90,55,50", None, "0,0,0"], 5.0)         # purple + yellow-green (awkward)
    add(["180,55,50", "0,55,50", None, "0,0,0"], 5.5)          # teal + red (complement, medium sat)
    add(["30,40,60", "120,40,50", "240,40,45", "0,0,0"], 6.0)  # three-way split at moderate sat
    add(["0,0,80", "0,0,80", "0,0,80", "0,0,80"], 6.5)         # all same gray — safe but zero variety
    add(["210,25,30", "210,25,30", None, "210,25,30"], 5.5)     # identical navy everywhere — monotonous
    add(["330,60,55", "0,0,50", "150,55,45", "0,0,0"], 5.3)    # pink + gray + green coat (uneasy)
    add(["60,45,55", "0,0,30", None, "0,0,0"], 6.4)            # gold tee + charcoal (ok, simple)

    # ─────────────────────────────────────────────────────────────
    #  EXTRA TIER 4 — MORE BAD  (2.5 – 4.2)
    # ─────────────────────────────────────────────────────────────
    add(["0,85,65", "180,85,65", "90,85,65", "270,85,65"], 2.7)  # four-way high-sat chaos
    add(["60,90,70", "300,90,70", None, "120,90,70"], 2.9)      # yellow + magenta + green all vivid
    add(["150,80,60", "330,80,60", "60,80,60", "0,0,0"], 3.3)   # teal + red-pink + yellow (loud trio)
    add(["30,85,70", "210,85,70", "120,85,70", "0,0,0"], 3.1)   # orange + blue + green (vivid triadic)
    add(["0,80,55", "0,0,85", "120,85,60", "0,0,0"], 3.8)      # loud red + white + loud green coat
    add(["240,80,60", "60,80,60", "0,80,60", "0,0,0"], 3.6)    # blue + yellow + red all at 80% sat

    # ─────────────────────────────────────────────────────────────
    #  EXTRA TIER 5 — MORE TERRIBLE  (1.0 – 2.4)
    # ─────────────────────────────────────────────────────────────
    add(["30,100,75", "150,100,75", "270,100,75", "0,0,0"], 1.3) # orange + cyan + violet full-sat
    add(["90,100,65", "210,100,65", "330,100,65", "0,0,0"], 1.1) # lime + blue + pink full-sat
    add(["0,100,75", "120,100,75", "240,100,75", "60,100,75"], 1.0) # R+G+B+Y all max — total chaos
    add(["180,100,65", "60,100,65", "300,100,65", "0,100,65"], 1.5) # teal+yellow+magenta+red

    # ─────────────────────────────────────────────────────────────
    #  EXTRA — SHOES MATTER (same outfit, different shoe scores)
    # ─────────────────────────────────────────────────────────────
    add(["210,40,30", "0,0,85", None, "0,0,10"], 8.8)           # navy + white + black shoes (perfect)
    add(["210,40,30", "0,0,85", None, "120,80,60"], 6.5)        # navy + white + BRIGHT GREEN shoes (ruins it)
    add(["210,40,30", "0,0,85", None, "30,25,25"], 9.0)         # navy + white + brown shoes (classic)
    add(["0,0,10", "0,0,80", None, "0,100,65"], 5.8)            # black + gray + BRIGHT RED shoes (jarring)
    add(["0,0,10", "0,0,80", None, "0,0,10"], 8.5)              # black + gray + black shoes (safe but flat)
    add(["30,35,55", "0,0,10", None, "300,90,65"], 5.5)         # camel + black + NEON PINK shoes (loud)
    add(["30,35,55", "0,0,10", None, "30,20,25"], 7.1)          # camel + black + brown shoes (great)

    # ─────────────────────────────────────────────────────────────
    #  NEUTRALS vs COLORED MONOCHROME
    #  Neutral outfits (B/W/gray/navy/brown) = good, wearable
    #  All-same saturated color outfits = costume, bad
    # ─────────────────────────────────────────────────────────────

    # --- All-neutral outfits: GOOD (7.0 – 8.5) ---
    add(["0,0,0", "0,0,100", None, "0,0,0"], 8.8)              # black + white + black shoes — timeless
    add(["0,0,0", "0,0,60", None, "0,0,0"], 7.8)               # black + gray + black shoes — clean
    add(["0,0,0", "0,0,100", "0,0,40", "0,0,0"], 8.5)          # black + white + charcoal coat — sharp
    add(["0,0,100", "0,0,25", None, "0,0,10"], 8.0)             # white top + charcoal pants + black shoes
    add(["0,0,15", "0,0,70", "0,0,45", "0,0,5"], 7.8)          # dark + light gray + mid coat + black shoes
    add(["210,25,20", "0,0,85", None, "0,0,10"], 8.3)           # navy + off-white + black shoes (navy = neutral)
    add(["210,20,25", "0,0,60", "0,0,30", "30,15,20"], 8.0)     # navy + gray + dark coat + brown shoes
    add(["30,15,50", "0,0,10", None, "0,0,10"], 7.5)            # tan + black + black shoes — simple earth
    add(["0,0,0", "30,20,50", None, "30,15,25"], 7.8)           # black + tan + brown shoes

    # --- All-same saturated color: BAD (2.0 – 4.0) ---
    add(["0,70,50", "0,65,45", "0,75,55", "0,60,40"], 1.0)     # all red everything — looks like a mascot
    add(["120,70,45", "120,65,40", "120,75,50", "120,60,35"], 1.0) # all green — looks like a tree
    add(["240,70,50", "240,65,45", "240,75,55", "240,60,40"], 1.0) # all blue — too much
    add(["300,70,50", "300,65,45", None, "300,60,40"], 2.6)     # all purple/magenta — costume
    add(["60,70,55", "60,65,50", "60,75,60", "60,60,45"], 1.4)  # all yellow — overwhelming
    add(["30,70,55", "30,65,50", "30,75,60", "30,60,45"], 1.5)  # all orange — traffic cone
    add(["180,70,45", "180,65,40", None, "180,60,35"], 1.8)     # all teal — one-note
    add(["330,70,50", "330,65,45", "330,75,55", "330,60,40"], 1.5) # all pink — too matchy

    # --- Same color + one neutral = still bad but slightly better ---
    add(["0,70,50", "0,65,45", "0,0,10", "0,60,40"], 2.6)      # red + red + black coat + red shoes — mostly red
    add(["120,70,45", "120,65,40", "0,0,80", "120,60,35"], 2.2)  # green + green + white coat + green shoes
    add(["240,70,50", "240,65,45", "0,0,10", "240,60,40"], 2.0) # blue + blue + black coat + blue shoes

    # --- Neutral monochrome with variety = still good ---
    add(["0,0,10", "0,0,10", "0,0,10", "0,0,10"], 7.4)         # literally all black — wearable but flat
    add(["0,0,95", "0,0,95", None, "0,0,95"], 7.4)              # literally all white — wearable but flat
    add(["0,0,10", "0,0,10", None, "0,0,10"], 7.4)              # all black 3pc — classic, acceptable

    # Write all examples to CSV (overwrites old file)
    write_training_data()


if __name__ == "__main__":
    print("Generating training data...")
    generate_training_data()
    print("Done.")