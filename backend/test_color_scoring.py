"""
Test cases for color scoring system.
Run with: python backend/test_color_scoring.py
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.main import score_outfit_colors


def check_outfit_colors_compatible(top_color, bottom_color, outer_color=None, shoes_color=None) -> bool:
    """Compatibility check using color score threshold."""
    colors = [top_color, bottom_color, outer_color, shoes_color]
    score = score_outfit_colors(colors)
    return score >= 4.0


def test_color_combinations():
    """Test various color combinations and their scores."""
    
    print("=" * 70)
    print("COLOR SCORING TEST CASES")
    print("=" * 70)
    print()
    
    # Test cases: (description, [top, bottom, outer, shoes], expected_behavior)
    test_cases = [
        # Classic neutral combinations
        ("Classic black & white business", ["white", "black", "gray", "black"], "Should score high - neutral contrast"),
        ("All black outfit", ["black", "black", "black", "black"], "Should score high - monochrome neutral"),
        ("Navy & beige formal", ["beige", "navy", "navy", "brown"], "Should score high - neutral combo"),
        ("Gray business suit", ["white", "gray", "gray", "black"], "Should score high - neutral palette"),
        
        # Neutral with one accent
        ("Navy suit, white shirt, black shoes", ["white", "navy", "navy", "black"], "Should score high - mostly neutrals"),
        ("White top, blue jeans, gray jacket, black shoes", ["white", "blue", "gray", "black"], "Should score well - neutral base with one color"),
        
        # Too many bright colors
        ("Red, orange, yellow, pink", ["red", "orange", "yellow", "pink"], "Should score lower - too many brights"),
        ("Red, blue, green, purple", ["red", "blue", "green", "purple"], "Should score lower - multiple brights"),
        
        # Good contrast
        ("Black top, tan pants, gray jacket, brown shoes", ["black", "tan", "gray", "brown"], "Should score well - light/dark contrast"),
        ("White shirt, navy pants, brown jacket, black shoes", ["white", "navy", "brown", "black"], "Should score well - contrast + neutrals"),
        
        # Complementary colors with neutrals
        ("Blue jeans with orange accent", ["white", "blue", "gray", "orange"], "Complementary with neutral base"),
        ("Red top with green accent", ["red", "black", "gray", "green"], "Complementary but risky"),
        
        # Analogous colors
        ("Blue & navy tones", ["white", "blue", "navy", "black"], "Analogous with neutral base"),
        ("Brown & beige earth tones", ["beige", "brown", "tan", "brown"], "Analogous neutrals - should score well"),
        
        # Monochromatic (same color)
        ("All blue outfit", ["blue", "blue", "blue", "blue"], "Same bright color - should score lower"),
        ("All red outfit", ["red", "red", "red", "red"], "Same bright color - should fail"),
        
        # Real outfit examples - Business
        ("Business formal: white shirt, navy suit, black shoes", 
         ["white", "navy", "navy", "black"], 
         "Business outfit - should score very high"),
        
        ("Smart casual: gray shirt, navy pants, brown jacket, brown shoes",
         ["gray", "navy", "brown", "brown"],
         "Smart casual - should score well"),
        
        # Real outfit examples - Casual
        ("Black t-shirt, blue jeans, gray hoodie, white sneakers",
         ["black", "blue", "gray", "white"],
         "Casual outfit - should score well"),
        
        ("White tee, khaki pants, beige jacket, brown boots",
         ["white", "khaki", "beige", "brown"],
         "Casual earth tones - should score well"),
        
        # Bad combinations
        ("All red loud outfit",
         ["red", "red", "red", "red"],
         "All red - should score low/fail"),
        
        ("Rainbow outfit: pink, purple, yellow, green",
         ["pink", "purple", "yellow", "green"],
         "Multiple brights - should score low"),
        
        ("Clashing brights: red, blue, orange, green",
         ["red", "blue", "orange", "green"],
         "Too many competing colors - should fail"),
        
        # Edge cases
        ("Multicolor with neutrals", ["multicolor", "black", "gray", "black"], "Multicolor treated as neutral"),
        ("Missing outer layer", ["black", "white", None, "brown"], "Should handle None values"),
        ("Missing shoes", ["white", "navy", "gray", None], "Should handle missing shoes"),
    ]
    
    for description, colors, expected in test_cases:
        score = score_outfit_colors(colors)
        
        # Use first 4 colors for compatibility check (top, bottom, outer, shoes)
        top = colors[0] if len(colors) > 0 else None
        bottom = colors[1] if len(colors) > 1 else None
        outer = colors[2] if len(colors) > 2 else None
        shoes = colors[3] if len(colors) > 3 else None
        
        compatible = check_outfit_colors_compatible(top, bottom, outer, shoes)
        
        # Format colors for display with labels
        color_parts = []
        labels = ["Top", "Bottom", "Outer", "Shoes"]
        for i, color in enumerate(colors):
            if i < len(labels):
                color_parts.append(f"{labels[i]}: {color if color else 'None'}")
        color_str = ", ".join(color_parts)
        
        print(f"📋 {description}")
        print(f"   {color_str}")
        print(f"   Score: {score}/10")
        status = "✅ PASS" if compatible else "❌ FAIL"
        print(f"   Compatible: {status} (threshold: 4.0)")
        print(f"   Expected: {expected}")
        print()
    
    print("=" * 70)
    print("SCORING BREAKDOWN:")
    print("  0-3 points:  Neutrals (1-2+ neutral colors)")
    print("  0-3 points:  Brights (penalty for too many saturated colors)")
    print("  0-2 points:  Contrast (light + dark present)")
    print("  0-2 points:  Harmony (analogous or complementary hues)")
    print("  Total: 0-10 points")
    print()
    print("  Compatibility threshold: 4.0+ = acceptable outfit")
    print("=" * 70)


if __name__ == "__main__":
    test_color_combinations()
