"""
Train the color harmony ML model from collected training data.

Steps:
1. Collect training data using save_training_data() in aimodel.py
2. Run this script: python train_model.py
3. Model will be saved as color_model.pkl
4. score_outfit_ml() will automatically use it
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle
from pathlib import Path
from datetime import datetime
import shutil


def train_model():
    """Train the color harmony model from CSV data."""
    
    # Create timestamp for this training session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Load training data
    csv_file = Path(__file__).parent / "training_data.csv"
    
    if not csv_file.exists():
        print(f"❌ No training data found at {csv_file}")
        print("   Use save_training_data() to collect outfit ratings first!")
        return
    
    # Backup the current training data with timestamp
    backup_dir = Path(__file__).parent / "training_backups"
    backup_dir.mkdir(exist_ok=True)
    backup_csv = backup_dir / f"training_data_{timestamp}.csv"
    shutil.copy2(csv_file, backup_csv)
    print(f"📁 Backed up training data to: {backup_csv}")
    
    data = pd.read_csv(csv_file)
    print(f"📊 Loaded {len(data)} training examples from {csv_file}")
    
    if len(data) < 10:
        print("⚠️  Warning: Less than 10 examples. Need more data for good model!")
    
    # Split features (X) and target (y)
    X = data.drop('rating', axis=1)  # All 18 features
    y = data['rating']  # Your manual ratings
    
    print(f"   Features: {list(X.columns)}")
    print(f"   Ratings range: {y.min():.1f} - {y.max():.1f}")
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train Random Forest model
    print("\n🤖 Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate model
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    
    print(f"\n📈 Model Performance:")
    print(f"   Train R² score: {train_score:.3f}")
    print(f"   Test R² score: {test_score:.3f}")
    print(f"   Test MSE: {mse:.3f}")
    
    # Feature importance
    importances = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n🔍 Top 5 Important Features:")
    for idx, row in importances.head(5).iterrows():
        print(f"   {row['feature']}: {row['importance']:.3f}")
    
    # Save model
    model_file = Path(__file__).parent / "color_model.pkl"
    
    # Backup existing model if it exists
    if model_file.exists():
        backup_model = backup_dir / f"color_model_{timestamp}.pkl"
        shutil.copy2(model_file, backup_model)
        print(f"📁 Backed up old model to: {backup_model}")
    
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"\n✅ Model saved to {model_file}")
    print(f"   score_outfit_ml() will now use this trained model!")
    print(f"\n📂 Backups saved in: {backup_dir}")
    print(f"   - training_data_{timestamp}.csv")
    if model_file.exists():
        print(f"   - color_model_{timestamp}.pkl")


if __name__ == "__main__":
    train_model()
