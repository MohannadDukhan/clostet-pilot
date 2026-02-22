"""
Test the trained color harmony model with various outfit combinations.
"""

from app.aimodel import score_outfit_ml


def test_model():
    """Test the model with various outfit combinations."""
    
    print("🧪 Testing trained ML model with outfit examples\n")
    print("=" * 80)
    
    # Test cases with expected behavior - EXPANDED TRICKY EXAMPLES
    test_outfits = [
        # ========== NEUTRALS & BASICS ==========
        {
            "name": "Classic Black & White",
            "colors": ["black", "white", None, "black"],
            "hsvs": ["0,0,0", "0,0,100", None, "0,0,0"],
            "expected": "High (8-9)"
        },
        {
            "name": "All Black Everything",
            "colors": ["black", "black", None, "black"],
            "hsvs": ["0,0,0", "0,0,0", None, "0,0,0"],
            "expected": "High (8-9)"
        },
        {
            "name": "All White (Summer Look)",
            "colors": ["white", "white", None, "white"],
            "hsvs": ["0,0,100", "0,0,100", None, "0,0,95"],
            "expected": "High (8-9)"
        },
        {
            "name": "Gray Tonal Outfit",
            "colors": ["light-gray", "dark-gray", None, "charcoal"],
            "hsvs": ["0,0,70", "0,0,40", None, "0,0,20"],
            "expected": "High (8-9)"
        },
        {
            "name": "Beige & Tan (Earth Tones)",
            "colors": ["beige", "tan", None, "brown"],
            "hsvs": ["30,20,80", "35,30,60", None, "30,40,30"],
            "expected": "High (7-9)"
        },
        {
            "name": "Navy & Khaki (Preppy)",
            "colors": ["navy", "khaki", None, "brown"],
            "hsvs": ["210,100,25", "50,30,70", None, "30,40,35"],
            "expected": "High (7-9)"
        },
        
        # ========== TRICKY NEUTRALS + ONE POP COLOR ==========
        {
            "name": "Black Top + White Pants + Red Shoes (Pop)",
            "colors": ["black", "white", None, "red"],
            "hsvs": ["0,0,0", "0,0,100", None, "0,100,60"],
            "expected": "Medium-High? (6-8)"
        },
        {
            "name": "Gray + Navy + Burgundy Shoes",
            "colors": ["gray", "navy", None, "burgundy"],
            "hsvs": ["0,0,50", "210,100,25", None, "0,80,35"],
            "expected": "Medium-High (7-8)"
        },
        {
            "name": "White Shirt + Denim + Tan Shoes",
            "colors": ["white", "blue", None, "tan"],
            "hsvs": ["0,0,100", "210,60,50", None, "35,30,60"],
            "expected": "High (7-9)"
        },
        {
            "name": "Black + Olive Green + Brown",
            "colors": ["black", "olive", None, "brown"],
            "hsvs": ["0,0,0", "60,50,35", None, "30,40,30"],
            "expected": "Medium-High (7-8)"
        },
        
        # ========== MONOCHROMATIC VARIATIONS ==========
        {
            "name": "Light Pink + Dark Pink + White Shoes",
            "colors": ["light-pink", "dark-pink", None, "white"],
            "hsvs": ["350,20,95", "340,60,70", None, "0,0,100"],
            "expected": "Medium-High (7-8)"
        },
        {
            "name": "Pastel Blue + Navy + Light Blue Shoes",
            "colors": ["pastel-blue", "navy", None, "light-blue"],
            "hsvs": ["200,30,85", "210,100,25", None, "200,40,70"],
            "expected": "Medium-High (7-8)"
        },
        {
            "name": "Mustard + Yellow + Beige (All Yellows)",
            "colors": ["mustard", "yellow", None, "beige"],
            "hsvs": ["45,70,70", "60,80,90", None, "40,20,85"],
            "expected": "Medium (5-7)"
        },
        {
            "name": "Forest Green + Mint + Dark Green",
            "colors": ["forest-green", "mint", None, "dark-green"],
            "hsvs": ["120,80,30", "150,40,80", None, "120,100,20"],
            "expected": "Medium (6-7)"
        },
        
        # ========== ANALOGOUS COLORS (Close on Color Wheel) ==========
        {
            "name": "Blue + Teal + Navy (Cool Analogous)",
            "colors": ["blue", "teal", None, "navy"],
            "hsvs": ["210,80,50", "180,70,45", None, "210,100,25"],
            "expected": "Medium (5-7)"
        },
        {
            "name": "Red + Orange + Burgundy (Warm Analogous)",
            "colors": ["red", "orange", None, "burgundy"],
            "hsvs": ["0,80,60", "30,80,65", None, "0,80,35"],
            "expected": "Medium-Low (4-6)"
        },
        {
            "name": "Purple + Pink + Magenta",
            "colors": ["purple", "pink", None, "magenta"],
            "hsvs": ["270,60,50", "340,40,80", None, "300,70,60"],
            "expected": "Medium (5-7)"
        },
        {
            "name": "Yellow + Lime + Chartreuse",
            "colors": ["yellow", "lime", None, "chartreuse"],
            "hsvs": ["60,80,90", "75,70,70", None, "80,80,60"],
            "expected": "Low-Medium (4-6)"
        },
        
        # ========== COMPLEMENTARY COLORS (Opposite on Wheel) ==========
        {
            "name": "Navy + Burnt Orange + Black",
            "colors": ["navy", "burnt-orange", None, "black"],
            "hsvs": ["210,100,30", "25,80,55", None, "0,0,0"],
            "expected": "Medium-High (6-8)"
        },
        {
            "name": "Purple + Yellow + White",
            "colors": ["purple", "yellow", None, "white"],
            "hsvs": ["270,70,50", "60,80,90", None, "0,0,100"],
            "expected": "Medium (5-7)"
        },
        {
            "name": "Red + Green + Brown (Softened)",
            "colors": ["rust-red", "sage-green", None, "brown"],
            "hsvs": ["10,60,50", "100,30,60", None, "30,40,30"],
            "expected": "Medium-High (6-8)"
        },
        {
            "name": "Teal + Coral + Cream",
            "colors": ["teal", "coral", None, "cream"],
            "hsvs": ["180,70,50", "15,60,80", None, "40,15,95"],
            "expected": "Medium (5-7)"
        },
        
        # ========== TRIADIC COLORS (Evenly Spaced) ==========
        {
            "name": "Red + Blue + Yellow (Primary Triadic)",
            "colors": ["red", "blue", None, "yellow"],
            "hsvs": ["0,100,60", "210,100,60", None, "60,100,90"],
            "expected": "Low (2-4)"
        },
        {
            "name": "Orange + Green + Purple (Secondary Triadic)",
            "colors": ["orange", "green", None, "purple"],
            "hsvs": ["30,100,70", "120,100,50", None, "270,100,50"],
            "expected": "Low (2-4)"
        },
        {
            "name": "Muted Triadic (Rust + Olive + Plum)",
            "colors": ["rust", "olive", None, "plum"],
            "hsvs": ["15,70,50", "60,50,40", None, "280,50,45"],
            "expected": "Medium (4-6)"
        },
        
        # ========== PASTELS & SOFT COLORS ==========
        {
            "name": "Pastel Pink + Mint + Lavender + White",
            "colors": ["pastel-pink", "mint", "lavender", "white"],
            "hsvs": ["350,25,95", "150,30,85", "270,30,90", "0,0,100"],
            "expected": "Medium-High (6-8)"
        },
        {
            "name": "Baby Blue + Peach + Cream",
            "colors": ["baby-blue", "peach", None, "cream"],
            "hsvs": ["200,30,90", "20,40,95", None, "40,15,95"],
            "expected": "Medium-High (6-8)"
        },
        {
            "name": "Soft Gray + Dusty Rose + Taupe",
            "colors": ["soft-gray", "dusty-rose", None, "taupe"],
            "hsvs": ["0,5,75", "350,35,70", None, "30,25,55"],
            "expected": "High (7-9)"
        },
        
        # ========== EARTH TONES ==========
        {
            "name": "Rust + Olive + Tan + Brown",
            "colors": ["rust", "olive", "tan", "brown"],
            "hsvs": ["15,70,50", "60,50,40", "40,30,65", "30,40,30"],
            "expected": "High (7-8)"
        },
        {
            "name": "Terracotta + Sage + Cream",
            "colors": ["terracotta", "sage", None, "cream"],
            "hsvs": ["15,60,60", "100,25,65", None, "40,15,95"],
            "expected": "High (7-9)"
        },
        {
            "name": "Clay + Moss Green + Sand",
            "colors": ["clay", "moss-green", None, "sand"],
            "hsvs": ["20,50,55", "80,45,45", None, "45,25,75"],
            "expected": "High (7-8)"
        },
        
        # ========== BOLD CLASHES (Should Score Low) ==========
        {
            "name": "Hot Pink + Lime Green + Electric Blue",
            "colors": ["hot-pink", "lime", None, "electric-blue"],
            "hsvs": ["330,100,90", "75,100,80", None, "195,100,100"],
            "expected": "Very Low (1-3)"
        },
        {
            "name": "Bright Orange + Bright Purple + Yellow",
            "colors": ["bright-orange", "bright-purple", None, "yellow"],
            "hsvs": ["30,100,100", "270,100,80", None, "60,100,100"],
            "expected": "Very Low (1-3)"
        },
        {
            "name": "Red + Cyan + Magenta",
            "colors": ["red", "cyan", None, "magenta"],
            "hsvs": ["0,100,70", "180,100,80", None, "300,100,80"],
            "expected": "Very Low (1-3)"
        },
        {
            "name": "Neon Green + Neon Pink + Electric Yellow",
            "colors": ["neon-green", "neon-pink", None, "electric-yellow"],
            "hsvs": ["120,100,100", "330,100,100", None, "60,100,100"],
            "expected": "Very Low (1-3)"
        },
        
        # ========== SOPHISTICATED/BUSINESS LOOKS ==========
        {
            "name": "Charcoal Suit + White Shirt + Burgundy Tie",
            "colors": ["white", "charcoal", "burgundy", "black"],
            "hsvs": ["0,0,100", "0,0,25", "0,80,35", "0,0,0"],
            "expected": "High (8-9)"
        },
        {
            "name": "Navy Blazer + Gray Pants + Brown Shoes",
            "colors": ["gray", "navy", None, "brown"],
            "hsvs": ["0,0,50", "210,100,30", None, "30,40,35"],
            "expected": "High (8-9)"
        },
        {
            "name": "Black Suit + Charcoal Shirt + Silver Tie",
            "colors": ["charcoal", "black", "silver", "black"],
            "hsvs": ["0,0,30", "0,0,0", "0,0,75", "0,0,0"],
            "expected": "High (8-9)"
        },
        
        # ========== DENIM COMBOS ==========
        {
            "name": "Blue Denim + White Tee + White Sneakers",
            "colors": ["white", "denim-blue", None, "white"],
            "hsvs": ["0,0,100", "210,60,45", None, "0,0,95"],
            "expected": "High (8-9)"
        },
        {
            "name": "Black Denim + Gray Hoodie + Black Shoes",
            "colors": ["gray", "black-denim", None, "black"],
            "hsvs": ["0,0,50", "210,30,15", None, "0,0,0"],
            "expected": "High (8-9)"
        },
        {
            "name": "Light Denim + Striped Shirt + Brown Boots",
            "colors": ["navy-white-stripe", "light-denim", None, "brown"],
            "hsvs": ["210,50,50", "210,40,70", None, "30,40,35"],
            "expected": "High (7-9)"
        },
        
        # ========== SEASONAL LOOKS ==========
        {
            "name": "Fall: Burgundy + Mustard + Brown + Tan",
            "colors": ["burgundy", "mustard", "brown", "tan"],
            "hsvs": ["0,80,35", "45,70,70", "30,40,30", "35,30,60"],
            "expected": "Medium-High (6-8)"
        },
        {
            "name": "Spring: Lavender + Mint + White + Nude",
            "colors": ["lavender", "mint", "white", "nude"],
            "hsvs": ["270,30,90", "150,30,85", "0,0,100", "25,15,85"],
            "expected": "High (7-9)"
        },
        {
            "name": "Summer: Coral + White + Denim + Tan",
            "colors": ["white", "denim", "coral", "tan"],
            "hsvs": ["0,0,100", "210,60,50", "15,60,80", "35,30,60"],
            "expected": "Medium-High (6-8)"
        },
        {
            "name": "Winter: Emerald + Cream + Navy + Black",
            "colors": ["cream", "emerald", "navy", "black"],
            "hsvs": ["40,15,95", "150,80,40", "210,100,25", "0,0,0"],
            "expected": "Medium-High (7-8)"
        },
        
        # ========== EDGE CASES & UNUSUAL COMBOS ==========
        {
            "name": "Neon Accent: Black + Black + Neon Yellow Shoes",
            "colors": ["black", "black", None, "neon-yellow"],
            "hsvs": ["0,0,0", "0,0,0", None, "60,100,100"],
            "expected": "Medium (4-7)"
        },
        {
            "name": "Metallic: Silver Top + Black Pants + Gold Shoes",
            "colors": ["silver", "black", None, "gold"],
            "hsvs": ["0,0,75", "0,0,0", None, "45,60,70"],
            "expected": "Medium (5-7)"
        },
        {
            "name": "Ombre Effect: Light Blue → Medium Blue → Dark Blue",
            "colors": ["light-blue", "medium-blue", "dark-blue", "navy"],
            "hsvs": ["200,40,80", "210,60,55", "210,80,35", "210,100,25"],
            "expected": "High (7-9)"
        },
        {
            "name": "Color Block: Red Top + Blue Pants + Yellow Jacket",
            "colors": ["red", "blue", "yellow", "white"],
            "hsvs": ["0,80,65", "210,80,50", "60,80,85", "0,0,100"],
            "expected": "Low (2-4)"
        },
    ]
    
    # Run tests
    results = []
    for i, outfit in enumerate(test_outfits, 1):
        score = score_outfit_ml(outfit["colors"], outfit["hsvs"])
        results.append({
            "outfit": outfit,
            "score": score
        })
        
        print(f"\n{i}. {outfit['name']}")
        print(f"   Colors: {outfit['colors']}")
        print(f"   HSVs: {outfit['hsvs']}")
        print(f"   Expected: {outfit['expected']}")
        print(f"   ✅ ML Score: {score:.1f}/10")
    
    print("\n" + "=" * 80)
    print("\n📊 SUMMARY OF ALL PREDICTIONS:\n")
    
    # Group by score ranges
    high_scores = [r for r in results if r["score"] >= 8.0]
    medium_high = [r for r in results if 6.5 <= r["score"] < 8.0]
    medium = [r for r in results if 5.0 <= r["score"] < 6.5]
    low = [r for r in results if r["score"] < 5.0]
    
    print(f"🟢 High Scores (8.0-10.0): {len(high_scores)} outfits")
    for r in high_scores:
        print(f"   • {r['outfit']['name']}: {r['score']:.1f}")
    
    print(f"\n🟡 Medium-High Scores (6.5-7.9): {len(medium_high)} outfits")
    for r in medium_high:
        print(f"   • {r['outfit']['name']}: {r['score']:.1f}")
    
    print(f"\n🟠 Medium Scores (5.0-6.4): {len(medium)} outfits")
    for r in medium:
        print(f"   • {r['outfit']['name']}: {r['score']:.1f}")
    
    print(f"\n🔴 Low Scores (0.0-4.9): {len(low)} outfits")
    for r in low:
        print(f"   • {r['outfit']['name']}: {r['score']:.1f}")
    
    print("\n" + "=" * 80)
    print(f"\n✅ Tested {len(test_outfits)} outfit combinations")
    print(f"   Average score: {sum(r['score'] for r in results) / len(results):.2f}/10")
    print(f"   Score range: {min(r['score'] for r in results):.1f} - {max(r['score'] for r in results):.1f}")


if __name__ == "__main__":
    test_model()
