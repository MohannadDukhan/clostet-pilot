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
    Extract 18 color harmony features from HSV values.
    
    Args:
        hsvs: List of HSV strings [top, bottom, outer, shoes]
    
    Returns:
        List of 18 numeric features for ML model
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
    
    top_hsv = parsed_hsvs[0]
    bottom_hsv = parsed_hsvs[1]
    outer_hsv = parsed_hsvs[2]
    shoes_hsv = parsed_hsvs[3]

    # Hue distance features
    diff_btw_top_bottom = hue_distance(top_hsv[0], bottom_hsv[0])
    diff_btw_top_outer = hue_distance(top_hsv[0], outer_hsv[0]) if outer_hsv else 0
    diff_btw_top_shoes = hue_distance(top_hsv[0], shoes_hsv[0])
    diff_btw_bottom_outer = hue_distance(bottom_hsv[0], outer_hsv[0]) if outer_hsv else 0
    diff_btw_bottom_shoes = hue_distance(bottom_hsv[0], shoes_hsv[0])
    diff_btw_shoes_outer = hue_distance(shoes_hsv[0], outer_hsv[0]) if outer_hsv else 0
    
    # Feature: has outer layer (1 or 0)
    has_outer = 1 if outer_hsv else 0
    
    # Saturation features
    saturations = [hsv[1] for hsv in parsed_hsvs if hsv is not None]
    avg_saturation = sum(saturations) / len(saturations)
    neutral_count = sum(1 for s in saturations if s < 20)
    
    # Value/Brightness features
    values = [hsv[2] for hsv in parsed_hsvs if hsv is not None]
    avg_value = sum(values) / len(values)
    has_light = 1 if any(v > 70 for v in values) else 0
    has_dark = 1 if any(v < 30 for v in values) else 0
    has_contrast = 1 if (has_light and has_dark) else 0
    
    # Harmony classification
    all_distances = [diff_btw_top_bottom, diff_btw_top_shoes, diff_btw_bottom_shoes]
    if outer_hsv:
        all_distances.extend([diff_btw_top_outer, diff_btw_bottom_outer, diff_btw_shoes_outer])
    
    has_monochrome = 1 if any(d < 15 for d in all_distances) else 0
    has_analogous = 1 if any(15 <= d <= 30 for d in all_distances) else 0
    has_complementary = 1 if any(150 <= d <= 210 for d in all_distances) else 0
    has_clash = 1 if any(60 <= d <= 120 for d in all_distances) else 0
    avg_hue_distance = sum(all_distances) / len(all_distances)
    
    # Return all features in consistent order
    return [
        diff_btw_top_bottom, diff_btw_top_shoes, diff_btw_bottom_shoes,
        diff_btw_top_outer, diff_btw_bottom_outer, diff_btw_shoes_outer,
        has_outer,
        avg_saturation, neutral_count,
        avg_value, has_light, has_dark, has_contrast,
        has_monochrome, has_analogous, has_complementary, has_clash,
        avg_hue_distance
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
            print(f"Input HSVs: {hsvs}")
            print(f"\nExtracted Features (18 total):")
            print(f"  • Hue distances: {features[:6]}")
            print(f"  • Has outer: {features[6]}")
            print(f"  • Saturation (avg={features[7]:.1f}, neutrals={features[8]})")
            print(f"  • Brightness (avg={features[9]:.1f}, light={features[10]}, dark={features[11]}, contrast={features[12]})")
            print(f"  • Harmony (mono={features[13]}, analogous={features[14]}, complementary={features[15]}, clash={features[16]})")
            print(f"  • Avg hue distance: {features[17]:.1f}°")
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
            'diff_top_bottom', 'diff_top_shoes', 'diff_bottom_shoes',
            'diff_top_outer', 'diff_bottom_outer', 'diff_shoes_outer',
            'has_outer', 'avg_saturation', 'neutral_count',
            'avg_value', 'has_light', 'has_dark', 'has_contrast',
            'has_monochrome', 'has_analogous', 'has_complementary', 'has_clash',
            'avg_hue_distance', 'rating'
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
    # ===== GOOD / SAFE (monochrome & analogous) =====
    add(["210,90,30", "215,70,35", None, "0,0,0"], 8.4)  # Navy + navy-blue → clean monochrome
    add(["30,50,70", "20,45,65", None, "0,0,0"], 8.0)   # Beige + tan → soft earth tones
    add(["240,70,40", "225,65,45", None, "0,0,0"], 8.3) # Blue → slightly greener blue
    add(["0,0,85", "0,0,60", None, "0,0,0"], 8.7)       # White + light gray → classic neutral
    add(["120,35,45", "110,30,40", None, "0,0,0"], 7.6) # Muted greens → calm, safe
    add(["280,45,60", "260,40,55", None, "0,0,0"], 7.9) # Soft purple tones
    add(["210,80,30", "0,0,80", None, "0,0,0"], 8.2)    # Navy + white → timeless
    add(["30,60,60", "0,0,85", None, "0,0,0"], 8.1)     # Camel + white → classy
    add(["200,55,45", "180,50,50", None, "0,0,0"], 7.7) # Blue → teal (analogous)
    add(["0,0,70", "0,0,40", None, "0,0,0"], 7.0)       # Gray on gray → safe but boring
    add(["10,10,10", "15,15,15", None, "0,0,0"], 7.8)   # Dark brown + slightly lighter brown
    add(["150,40,50", "160,35,45", None, "0,0,0"], 7.5) # Olive green + muted green
    add(["330,50,60", "340,45,55", None, "0,0,0"], 7.3) # Muted rose + dusty pink
    add(["45,60,70", "0,0,80", None, "0,0,0"], 7.9)     # Cream + white
    add(["210,60,20", "220,55,25", "200,65,20", "0,0,0"], 8.5) # Three shades of blue
    # ===== GOOD BUT BOLD (Complementary + Neutrals, Triadic) =====
    add(["240,80,50", "0,0,70", None, "30,50,45"], 7.4) # Blue + gray + brown shoes
    add(["0,70,60", "0,0,50", None, "0,0,0"], 7.6)      # Red accent with neutral base
    add(["120,55,50", "0,0,70", None, "0,0,0"], 7.0)    # Green + gray
    add(["30,65,60", "0,0,40", None, "240,60,45"], 7.3) # Orange + dark neutral + blue shoes
    add(["210,75,30", "0,0,80", "30,45,40", "0,0,0"], 7.2) # Navy + white + brown jacket
    add(["280,60,50", "0,0,60", None, "30,50,40"], 7.1) # Purple with earth neutral
    add(["240,70,50", "0,0,40", None, "0,0,0"], 6.8)    # Blue + charcoal
    add(["60,65,60", "0,0,50", None, "0,0,0"], 6.7)     # Yellow accent, toned down
    add(["180,60,50", "0,0,40", None, "0,0,0"], 6.6)    # Teal + charcoal
    add(["300,60,60", "0,0,40", None, "0,0,0"], 6.9)    # Pink accent with dark base
    add(["0,70,50", "180,70,50", None, "0,0,0"], 7.5)   # Red + Teal (complementary)
    add(["60,70,50", "240,70,50", None, "0,0,0"], 7.3)  # Yellow + Purple (complementary)
    add(["120,70,50", "300,70,50", None, "0,0,0"], 7.2) # Green + Magenta (complementary)
    add(["210,60,40", "30,60,40", "0,0,70", "0,0,0"], 7.7) # Blue + Orange + Light Gray
    add(["150,60,40", "330,60,40", "0,0,70", "0,0,0"], 7.6) # Green-Blue + Red-Purple + Light Gray
    add(["0,0,90", "210,80,30", "30,70,60", "0,0,0"], 7.8) # White + Navy + Orange (triadic-ish)
    # ===== AVERAGE / OK =====
    add(["0,55,55", "210,50,45", None, "0,0,0"], 6.1)   # Red + blue (balanced saturation)
    add(["120,50,50", "30,45,50", None, "0,0,0"], 5.9) # Green + brown
    add(["240,50,50", "60,50,55", None, "0,0,0"], 5.6) # Blue + yellow (muted)
    add(["30,60,60", "210,55,50", None, "0,0,0"], 5.8) # Orange + blue
    add(["280,50,55", "120,45,45", None, "0,0,0"], 5.5) # Purple + green (muted clash)
    add(["60,55,55", "240,55,50", None, "0,0,0"], 5.7)
    add(["180,45,50", "30,45,50", None, "0,0,0"], 5.4)
    add(["300,50,55", "210,50,50", None, "0,0,0"], 5.8)
    add(["120,40,40", "0,0,60", None, "0,0,0"], 6.0)
    add(["210,40,40", "0,0,60", None, "0,0,0"], 6.1)
    add(["0,0,50", "0,0,70", "210,30,40", "0,0,0"], 6.5) # Dark gray + light gray + muted blue
    add(["90,50,50", "270,50,50", None, "0,0,0"], 5.3) # Yellow-green + Red-violet (split complementary)
    add(["30,50,40", "210,50,40", "0,0,80", "0,0,0"], 6.2) # Muted orange + muted blue + white
    add(["0,0,30", "0,0,60", "0,0,90", "0,0,0"], 6.8) # Dark, medium, light gray
    add(["340,40,50", "160,40,50", None, "0,0,0"], 5.2) # Dusty rose + sage green
    # ===== BAD / CLASHING =====
    add(["0,100,60", "120,100,60", None, "300,100,60"], 2.4) # Red + green + magenta (high saturation)
    add(["60,100,60", "240,100,60", None, "0,100,60"], 2.0) # Yellow + Purple + Red
    add(["120,100,60", "300,100,60", None, "30,100,60"], 2.3) # Green + Magenta + Orange
    add(["0,100,65", "240,100,65", None, "120,100,65"], 1.9) # Red + Blue + Green
    add(["300,100,60", "60,100,60", None, "240,100,60"], 2.1) # Magenta + Yellow + Blue
    add(["120,90,50", "30,90,50", None, "240,90,50"], 2.5) # Green + Orange + Blue
    add(["0,100,70", "180,100,70", None, "90,100,70"], 1.8) # Red + Teal + Lime Green
    add(["240,100,60", "30,100,60", None, "120,100,60"], 2.2) # Blue + Orange + Green
    add(["60,100,60", "300,100,60", None, "0,100,60"], 2.0) # Yellow + Magenta + Red
    add(["180,100,60", "0,100,60", None, "300,100,60"], 1.9) # Teal + Red + Magenta
    add(["210,100,60", "30,100,60", None, "150,100,60"], 1.7) # Blue + Orange + Green-Blue
    add(["0,100,50", "60,100,50", "120,100,50", "0,0,0"], 2.8) # Red + Yellow + Green
    add(["270,100,60", "90,100,60", None, "0,0,0"], 2.6) # Violet + Lime Green
    # ===== WITH OUTERWEAR (Good Layering) =====
    add(["210,75,30", "0,0,80", "30,45,40", "0,0,0"], 7.8) # Navy + white + brown jacket
    add(["240,65,40", "0,0,70", "210,60,35", "0,0,0"], 7.4) # Blue layers
    add(["0,70,60", "0,0,50", "0,0,30", "0,0,0"], 7.9)     # Red with dark neutral coat
    add(["120,60,50", "30,60,50", "0,0,40", "0,0,0"], 5.8) # Green + brown + gray coat (acceptable)
    add(["300,70,60", "240,70,50", "0,0,40", "0,0,0"], 6.4) # Purple + blue + neutral coat
    add(["0,0,90", "210,40,30", "30,30,20", "0,0,0"], 8.1) # White + muted blue + dark muted orange jacket
    add(["30,60,50", "0,0,70", "120,30,30", "0,0,0"], 7.6) # Muted orange + light neutral + olive jacket
    add(["180,50,40", "0,0,80", "270,30,40", "0,0,0"], 7.5) # Teal + white + muted violet jacket
    # ===== WITH OUTERWEAR (Bad Layering) =====
    add(["210,80,30", "0,0,80", "120,80,50", "0,0,0"], 5.0) # Green jacket ruins navy base
    add(["30,70,60", "0,0,60", "300,80,55", "0,0,0"], 4.6) # Loud pink jacket
    add(["0,100,60", "0,0,90", "60,100,60", "0,0,0"], 3.5) # Bright red + white + bright yellow jacket
    add(["240,90,50", "0,0,40", "30,90,70", "0,0,0"], 4.0) # Blue + dark neutral + bright orange jacket
    # ===== More Monochrome/Analogous (Higher Scores) =====
    add(["200,80,40", "195,75,35", "205,85,45", None], 8.7) # closely related blues
    add(["50,40,60", "55,35,55", "45,45,65", None], 8.2) # Earthy yellows
    add(["320,60,50", "315,55,45", "325,65,55", None], 8.3) # Deep purples
    add(["10,10,20", "12,12,22", "8,8,18", None], 8.0) # Very dark monochromatic
    add(["0,0,10", "0,0,15", "0,0,5", None], 8.1) # Grayscale, very dark
    # ===== More Complementary/Triadic (Mid to High Scores) =====
    add(["210,70,50", "30,70,50", "0,0,80", None], 7.9) # Blue + Orange + White
    add(["120,60,50", "300,60,50", "0,0,40", None], 7.5) # Green + Magenta + Dark Gray
    add(["0,60,50", "180,60,50", "0,0,70", None], 7.7) # Red + Teal + Light Gray
    add(["60,60,50", "240,60,50", "0,0,30", None], 7.3) # Yellow + Purple + Very Dark Gray
    add(["15,70,40", "195,70,40", "0,0,90", None], 7.8) # Orange-red + Blue-green + White
    # ===== More Neutral Combinations (Mid Scores) =====
    add(["0,0,20", "0,0,40", "0,0,60", None], 7.0) # Dark to light gray
    add(["0,0,70", "30,10,30", "0,0,0", None], 7.2) # Light gray + muted brown + black
    add(["40,20,50", "0,0,85", "0,0,0", None], 7.1) # Muted olive + white + black
    add(["250,15,30", "0,0,80", "0,0,50", None], 7.4) # Muted blue + white + medium gray
    # ===== More "Average" Combinations (Mid-Range Scores) =====
    add(["20,60,50", "200,60,50", None, "0,0,0"], 5.9) # Muted orange-yellow + muted blue
    add(["100,50,45", "280,50,45", None, "0,0,0"], 5.7) # Yellow-green + Violet
    add(["330,55,50", "150,55,50", None, "0,0,0"], 5.6) # Magenta-pink + olive green
    add(["230,45,60", "50,45,60", None, "0,0,0"], 6.0) # Light blue + light yellow
    # ===== More "Bad" Combinations (Low Scores) =====
    add(["10,100,70", "130,100,70", "250,100,70", "0,0,0"], 1.5) # Three highly saturated, clashing colors
    add(["0,100,80", "180,100,80", "90,100,80", "0,0,0"], 1.0) # Bright red + bright teal + bright lime
    add(["30,100,90", "210,100,90", None, "0,0,0"], 2.0) # Very light, saturated orange + bright blue
    add(["270,100,60", "45,100,60", None, "0,0,0"], 2.2) # Saturated violet + saturated chartreuse
    # ===== Combinations with Black and White (Varying Scores) =====
    add(["0,0,0", "0,0,100", "210,70,40", None], 7.8) # Black + White + Blue
    add(["0,0,0", "0,0,100", "0,70,50", None], 7.0) # Black + White + Red
    add(["0,0,0", "0,0,100", "60,70,50", None], 6.5) # Black + White + Yellow
    add(["0,0,0", "210,70,40", "30,60,50", None], 6.8) # Black + Blue + Orange (bold, but can work)
    add(["0,0,100", "120,80,50", "300,80,50", None], 5.0) # White + Green + Magenta (can be jarring)
    # ===== Further Monochrome/Analogous =====
    add(["220,50,30", "230,45,25", "215,55,35", None], 8.6) # Deep blues
    add(["160,30,40", "170,25,35", "155,35,45", None], 8.1) # Muted blue-greens
    add(["20,40,70", "25,35,65", "15,45,75", None], 8.0) # Light earthy tones
    add(["350,60,50", "345,55,45", "355,65,55", None], 8.4) # Rich reds
    add(["70,50,60", "65,45,55", "75,55,65", None], 8.2) # Muted yellows
    add(["290,50,40", "300,45,35", "285,55,45", None], 8.3) # Violet-blues
    # ===== Further Bold Combinations =====
    add(["200,80,60", "20,80,60", "0,0,70", None], 7.1) # Blue-Purple + Orange + Light Gray
    add(["100,70,50", "280,70,50", "0,0,40", None], 7.0) # Lime Green + Purple + Dark Gray
    add(["30,75,65", "210,75,65", "0,0,85", None], 7.6) # Bright Orange + Bright Blue + White
    add(["0,70,40", "120,70,40", "240,70,40", None], 6.8) # Red + Green + Blue (triadic, high saturation)
    add(["45,65,55", "165,65,55", "285,65,55", None], 6.9) # Split Complementary (Green-yellow + Blue-violet + Red-violet)
    # ===== Further Average/OK Combinations =====
    add(["0,40,50", "180,40,50", None, "0,0,0"], 5.5) # Muted Red + Muted Teal
    add(["90,30,40", "270,30,40", None, "0,0,0"], 5.4) # Muted Green-Yellow + Muted Violet
    add(["30,50,70", "210,40,60", "0,0,80", None], 6.3) # Light Orange + Muted Blue + White
    add(["50,20,30", "0,0,60", "0,0,30", None], 6.2) # Muted Yellow + Medium Gray + Dark Gray
    # ===== Further Bad/Clashing Combinations =====
    add(["70,100,80", "190,100,80", "310,100,80", "0,0,0"], 1.2) # Three super bright, clashing pastels
    add(["10,100,30", "130,100,30", "250,100,30", "0,0,0"], 1.1) # Three super dark, saturated, clashing colors
    add(["0,100,90", "120,100,90", None, "0,0,0"], 2.0) # Super light, saturated Red + Green
    # ===== More Outerwear (Good) =====
    add(["0,0,95", "240,50,30", "210,40,25", "0,0,0"], 8.0) # Very light neutral + muted blue + darker muted blue jacket
    add(["30,50,40", "0,0,85", "150,30,35", "0,0,0"], 7.7) # Muted orange + white + olive jacket
    add(["210,60,30", "0,0,70", "330,40,40", "0,0,0"], 7.5) # Blue + light neutral + muted berry jacket
    # ===== More Outerwear (Bad) =====
    add(["20,100,70", "0,0,90", "200,100,70", "0,0,0"], 3.0) # Bright yellow-orange + white + bright blue jacket
    add(["100,90,50", "0,0,30", "280,90,50", "0,0,0"], 3.2) # Bright lime green + dark neutral + bright purple jacket
    
    # Write all examples to CSV (overwrites old file)
    write_training_data()


if __name__ == "__main__":
    print("Generating training data...")
    generate_training_data()
    print("Done.")