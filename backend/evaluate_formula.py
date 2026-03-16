"""
evaluate_formula.py
-------------------
Compares three things for every training example:
  1. The ACTUAL rating (human-labelled, from training_data.csv)
  2. The FORMULA score  (explicit rule-based function below)
  3. The MODEL score    (model.predict, if color_model.pkl exists)

Prints a row for each example, then overall MAE for both.
"""

import csv
import pickle
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
#  EXPLICIT SCORING FORMULA
#────────

def formula_score(avg_hue_distance, avg_saturation, high_sat_count,
                  neutral_count, has_contrast) -> float:
    clash_loudness = (avg_hue_distance / 180.0) * (avg_saturation / 100.0)

    raw = (
          5.0
        + min(neutral_count, 2) * 1.2   # neutral anchors
        - high_sat_count        * 1.   # loud pieces penalty
        - clash_loudness        * 3.5   # hue-clash × saturation penalty
        + has_contrast          * 2.0   # contrast bonus
    )
    return round(max(1.0, min(raw, 10.0)), 1)


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD MODEL (optional)
# ─────────────────────────────────────────────────────────────────────────────

MODEL_PATH = Path(__file__).parent / "color_model.pkl"
model = None
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print(f"Loaded model from {MODEL_PATH}\n")
except FileNotFoundError:
    print("No model found — only formula scores will be shown.\n")
except Exception as e:
    print(f"Could not load model ({e}) — only formula scores will be shown.\n")


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD TRAINING DATA
# ─────────────────────────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent / "training_data.csv"
rows = []
with open(CSV_PATH, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            "avg_hue_distance": float(row["avg_hue_distance"]),
            "max_hue_distance": float(row["max_hue_distance"]),
            "avg_saturation":   float(row["avg_saturation"]),
            "high_sat_count":   float(row["high_sat_count"]),
            "neutral_count":    float(row["neutral_count"]),
            "has_contrast":     float(row["has_contrast"]),
            "actual":           float(row["rating"]),
        })


# ─────────────────────────────────────────────────────────────────────────────
#  RUN COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

formula_errors = []
model_errors   = []
fm_errors      = []  # formula vs model

if model:
    header = f"{'#':>4}  {'Actual':>7}  {'Formula':>8}  {'F-Err':>7}  {'Model':>7}  {'M-Err':>7}"
else:
    header = f"{'#':>4}  {'Actual':>7}  {'Formula':>8}  {'F-Err':>7}"

print(header)
print("-" * len(header))

for i, r in enumerate(rows, 1):
    fs = formula_score(
        r["avg_hue_distance"],
        r["avg_saturation"],
        r["high_sat_count"],
        r["neutral_count"],
        r["has_contrast"],
    )
    f_err = abs(fs - r["actual"])
    formula_errors.append(f_err)

    if model:
        features = [
            r["avg_hue_distance"],
            r["max_hue_distance"],
            r["avg_saturation"],
            r["high_sat_count"],
            r["neutral_count"],
            r["has_contrast"],
        ]
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            ms = round(float(model.predict([features])[0]), 1)
        ms = max(0.0, min(ms, 10.0))
        m_err = abs(ms - r["actual"])
        model_errors.append(m_err)
        fm_errors.append(abs(fs - ms))
        print(f"{i:>4}  {r['actual']:>7.1f}  {fs:>8.1f}  {f_err:>7.2f}  {ms:>7.1f}  {m_err:>7.2f}")
    else:
        print(f"{i:>4}  {r['actual']:>7.1f}  {fs:>8.1f}  {f_err:>7.2f}")


# ─────────────────────────────────────────────────────────────────────────────
#  SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

n = len(rows)
f_mae  = sum(formula_errors) / n
f_pct  = (f_mae / 10.0) * 100

print("\n" + "=" * 58)
print(f"  Examples evaluated          : {n}")
print(f"  Actual  vs Formula  (MAE)   : {f_mae:.3f}  ({f_pct:.1f}% of 10-pt scale)")

if model_errors:
    m_mae = sum(model_errors) / n
    m_pct = (m_mae / 10.0) * 100
    fm_mae = sum(fm_errors) / n
    fm_pct = (fm_mae / 10.0) * 100
    print(f"  Actual  vs Model    (MAE)   : {m_mae:.3f}  ({m_pct:.1f}% of 10-pt scale)")
    print(f"  Formula vs Model    (MAE)   : {fm_mae:.3f}  ({fm_pct:.1f}% of 10-pt scale)")

print("=" * 58)
