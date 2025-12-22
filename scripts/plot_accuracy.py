#!/usr/bin/env python
import os, sys, joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Allow imports if needed (not strictly used here but safe)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.ml_model import SimpleModel  # ensure this works

# --- Paths ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SERVER_SAVE_DIR = os.path.join(PROJECT_ROOT, "server_models")
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "aursad.csv")
PLOT_DIR = os.path.join(PROJECT_ROOT, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)
OUT_PATH = os.path.join(PLOT_DIR, "accuracy_plot.png")

# --- Load dataset ---
df = pd.read_csv(DATA_PATH)

# Separate features/label
X = df.iloc[:, :-1]
y_raw = df.iloc[:, -1].copy()

# *** LABEL REMAP: adjust this to your dataset semantics ***
# Example: anomaly=1, normal=0 (non-zero -> anomaly)
y = (y_raw != 0).astype(int)

# Train/test split (stable)
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Scale using TRAIN split only
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(X_train)
X_test_scaled = scaler.transform(X_test)

# --- Scan server models ---
files = [f for f in os.listdir(SERVER_SAVE_DIR) if f.startswith("global_round_") and f.endswith(".joblib")]
if not files:
    print("No global_round_* files found in", SERVER_SAVE_DIR)
    sys.exit(0)

# Parse round numbers safely
def extract_round(fname: str) -> int:
    # expect global_round_<N>.joblib
    stem = os.path.splitext(fname)[0]
    parts = stem.split("_")
    # find last numeric token
    for token in reversed(parts):
        if token.isdigit():
            return int(token)
    raise ValueError(f"Cannot extract round from filename: {fname}")

parsed = []
for f in files:
    try:
        r = extract_round(f)
        parsed.append((r, f))
    except Exception as e:
        print(f"Skipping {f}: {e}")

# Sort by round ascending
parsed.sort(key=lambda x: x[0])

rounds = []
accuracies = []

print(f"Found {len(parsed)} global model files.")
for round_num, fname in parsed:
    path = os.path.join(SERVER_SAVE_DIR, fname)
    payload = joblib.load(path)

    if "weights" not in payload:
        print(f"[warn] {fname} missing 'weights' key; skipping.")
        continue

    w = payload["weights"]
    # instantiate model
    model = SimpleModel(input_size=X_test.shape[1])
    model.load_weights(w)

    acc = model.evaluate(X_test_scaled, y_test.to_numpy())
    rounds.append(round_num)
    accuracies.append(acc)
    print(f"Round {round_num}: acc={acc:.4f}")

# --- Plot ---
plt.figure(figsize=(8,5))
plt.plot(rounds, accuracies, marker='o')
plt.xlabel("Training Round")
plt.ylabel("Accuracy")
plt.ylim(0.0, 1.0)  # show full range
plt.title("Global Model Accuracy over Rounds")
plt.grid(True)
plt.tight_layout()
plt.savefig(OUT_PATH, dpi=150)
print(f"✅ Plot saved as {OUT_PATH}")
