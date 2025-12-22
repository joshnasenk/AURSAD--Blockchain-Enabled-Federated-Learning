import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
import numpy as np
import joblib
import traceback
import hashlib
from collections import defaultdict

from models.ml_model import SimpleModel
from client.merkle import merkle_root
from server.trust import trust_scores, update_trust

# ---------------- CONFIG ----------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SERVER_SAVE_DIR = os.path.join(BASE_DIR, "server_models")
os.makedirs(SERVER_SAVE_DIR, exist_ok=True)

app = Flask(__name__)

global_model = SimpleModel()
global_model_initialized = False

# Track per round
round_updates = defaultdict(list)
round_event_hashes = defaultdict(list)
round_counter = 0

# ---------------- UTILS ----------------
def save_global_model(round_idx, model):
    payload = {"weights": model.get_weights()}
    path_round = os.path.join(SERVER_SAVE_DIR, f"global_round_{round_idx}.joblib")
    path_latest = os.path.join(SERVER_SAVE_DIR, "global_latest.joblib")
    joblib.dump(payload, path_round)
    joblib.dump(payload, path_latest)
    print(f"[Server] 💾 Saved global model -> round {round_idx}")

def weighted_aggregate(models, trusts):
    total_weight = sum(trusts)
    coef_sum = None
    bias_sum = 0.0

    for m, t in zip(models, trusts):
        w = m["coefficients"]
        b = m["intercept"]

        if coef_sum is None:
            coef_sum = t * w
        else:
            coef_sum += t * w
        bias_sum += t * b

    return {
        "coefficients": coef_sum / total_weight,
        "intercept": bias_sum / total_weight
    }

# ---------------- ROUTES ----------------
@app.route("/upload_model", methods=["POST"])
def upload_model():
    global global_model_initialized, round_counter

    try:
        data = request.get_json()
        client_id = data["client_id"]
        round_id = data["round"]
        last_event_hash = data["last_event_hash"]

        weights = {
            "coefficients": np.array(data["coefficients"]),
            "intercept": data["intercept"]
        }

        # Record update
        round_updates[round_id].append((client_id, weights))
        round_event_hashes[round_id].append(last_event_hash)

        update_trust(client_id, success=True)

        print(f"[Server] 📥 Received update from {client_id} (round {round_id})")

        return "Update received", 200

    except Exception as e:
        update_trust(data.get("client_id", "unknown"), success=False)
        print(f"[Server] ❌ Upload error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/get_global_model", methods=["GET"])
def get_global_model():
    global global_model_initialized, round_counter

    try:
        round_counter += 1
        updates = round_updates.get(round_counter, [])

        if not updates:
            return jsonify({"error": "No updates for round"}), 404

        client_ids = [cid for cid, _ in updates]
        models = [w for _, w in updates]
        trusts = [trust_scores[cid] for cid in client_ids]

        agg_weights = weighted_aggregate(models, trusts)

        global_model.load_weights(agg_weights)
        global_model_initialized = True

        save_global_model(round_counter, global_model)

        proof_root = merkle_root(round_event_hashes[round_counter])

        response = {
            "coefficients": agg_weights["coefficients"].tolist(),
            "intercept": agg_weights["intercept"],
            "contributors": client_ids,
            "round": round_counter,
            "aggregation_proof": proof_root
        }

        print(f"[Server] 🔗 Aggregated round {round_counter}")
        return jsonify(response)

    except Exception as e:
        print(f"[Server] ❌ Aggregation error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
