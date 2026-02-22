"""
Migration script to add primary_color_hex and primary_color_hsv columns to the item table.
Run this once to update your existing database schema.
"""
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "outfitmaker.sqlite"


def migrate():
    """Add color_hex and color_hsv columns to item table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(item)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add primary_color_hex if it doesn't exist
        if "primary_color_hex" not in columns:
            print("Adding primary_color_hex column...")
            cursor.execute("ALTER TABLE item ADD COLUMN primary_color_hex TEXT")
            print("✓ primary_color_hex column added")
        else:
            print("primary_color_hex column already exists, skipping...")
        
        # Add primary_color_hsv if it doesn't exist
        if "primary_color_hsv" not in columns:
            print("Adding primary_color_hsv column...")
            cursor.execute("ALTER TABLE item ADD COLUMN primary_color_hsv TEXT")
            print("✓ primary_color_hsv column added")
        else:
            print("primary_color_hsv column already exists, skipping...")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
