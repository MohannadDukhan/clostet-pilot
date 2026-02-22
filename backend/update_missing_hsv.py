"""
Script to update items that are missing HSV data.
Run this once to analyze existing items.
"""
from sqlmodel import Session, select
from app.db import engine
from app.models import Item
from app.vision import analyze_item_color
from pathlib import Path

def update_missing_hsv():
    with Session(engine) as session:
        # Find all items without HSV data
        statement = select(Item).where(Item.primary_color_hsv == None)
        items = session.exec(statement).all()
        
        print(f"Found {len(items)} items missing HSV data\n")
        
        for item in items:
            print(f"Processing: {item.category} (ID: {item.id})")
            
            # Get image path
            user_folder = Path(__file__).parent / "storage" / str(item.user_id) / "items"
            image_path = user_folder / item.image_url
            
            if not image_path.exists():
                print(f"  ❌ Image not found: {image_path}")
                continue
            
            try:
                # Analyze with vision API
                color_info = analyze_item_color(str(image_path))
                
                if color_info and "color_hex" in color_info:
                    item.primary_color_hex = color_info["color_hex"]
                    item.primary_color_hsv = color_info.get("color_hsv")
                    
                    # Update color name if available
                    if "color_name" in color_info:
                        item.primary_color = color_info["color_name"]
                    
                    session.add(item)
                    print(f"  ✅ Updated: {item.primary_color} (hex={item.primary_color_hex}, hsv={item.primary_color_hsv})")
                else:
                    print(f"  ⚠️  No color data returned")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        session.commit()
        print(f"\n✅ Done! Updated {len(items)} items")

if __name__ == "__main__":
    update_missing_hsv()
