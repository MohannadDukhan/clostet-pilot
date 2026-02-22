"""
Reset training data - archives old data and starts fresh.

Run this when you want to start collecting new training data from scratch.
"""

from pathlib import Path
from datetime import datetime
import shutil


def reset_training_data():
    """Archive current training data and start fresh."""
    
    csv_file = Path(__file__).parent / "training_data.csv"
    
    if not csv_file.exists():
        print("ℹ️  No existing training data found. Nothing to reset.")
        return
    
    # Create archive directory
    archive_dir = Path(__file__).parent / "training_archives"
    archive_dir.mkdir(exist_ok=True)
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Archive current training data
    archive_csv = archive_dir / f"training_data_archived_{timestamp}.csv"
    shutil.move(str(csv_file), str(archive_csv))
    
    print(f"✅ Archived old training data to: {archive_csv}")
    print(f"📝 Ready to collect new training data!")
    print(f"\nNext steps:")
    print(f"   1. Run: python app/aimodel.py  (to generate new training examples)")
    print(f"   2. Run: python train_model.py   (to train a new model)")


if __name__ == "__main__":
    reset_training_data()
