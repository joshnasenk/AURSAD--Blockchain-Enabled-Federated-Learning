import time
import pandas as pd
import hashlib
import json
import requests
import sys
import gc
import threading
import os
from web3 import Web3
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample
from sklearn.metrics import f1_score
import joblib

from .events import create_event
from .model import SimpleModel
from .merkle import merkle_root


# ---------------- CONFIG ----------------
client_id = sys.argv[1] if len(sys.argv) > 1 else "main"
print(f"[Client {client_id}] Initializing...")

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
assert w3.is_connected(), f"[Client {client_id}] ❌ Web3 not connected"

private_key = "0x2962883fe387707b6a47c537c27d03c2918fc7bdb0f60939c25cdff07643b362"
account = "0x9c28885680b17b701956ddefB04DadB3a538070c"
contract_address = "0x83B69AEe9F8C1c171Be05e3259F9A1074cE5a91C"

with open("artifacts/contracts/DataVerification.sol/DataVerification.json") as f:
    abi = json.load(f)["abi"]
contract = w3.eth.contract(address=contract_address, abi=abi)

# ---------------- DATA ----------------
df = pd.read_csv("data/aursad.csv").sample(frac=1, random_state=42).reset_index(drop=True)
X = df.iloc[:, :-1]
y = df.iloc[:, -1]

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ---------------- MODEL ----------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

model = SimpleModel(input_size=X_train.shape[1])

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIENT_SAVE_DIR = os.path.join(BASE_DIR, "saved_models")
os.makedirs(CLIENT_SAVE_DIR, exist_ok=True)

# ---------------- EVENT STATE ----------------
event_chain = []
round_event_hashes = []
previous_event_hash = "GENESIS"

# ---------------- TRAINING CONFIG ----------------
max_training_rounds = 10
ROW_BATCH_FOR_UPDATE = 2000
training_counter = 0
data_buffer = []

# ---------------- UTILS ----------------
def hash_row(row):
    return hashlib.sha256(",".join(map(str, row)).encode()).hexdigest()

def log_event(event_type, payload):
    global previous_event_hash, event_chain, round_event_hashes
    event = create_event(
        event_type=event_type,
        client_id=client_id,
        payload=payload,
        prev_hash=previous_event_hash
    )
    event_chain.append(event)
    round_event_hashes.append(event["event_hash"])
    previous_event_hash = event["event_hash"]

def anchor_merkle_root(round_idx):
    root = merkle_root(round_event_hashes)
    root_bytes = bytes.fromhex(root)

    nonce = w3.eth.get_transaction_count(account)
    tx = contract.functions.recordRoundMerkleRoot(
        round_idx, root_bytes
    ).build_transaction({
        "from": account,
        "nonce": nonce,
        "gas": 2000000,
        "gasPrice": w3.to_wei("50", "gwei")
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"[Client {client_id}] 🔒 Anchored Merkle root for round {round_idx}")
    round_event_hashes.clear()

def send_model_to_server(round_idx):
    weights = model.get_weights()
    payload = {
        "client_id": client_id,
        "round": round_idx,
        "coefficients": weights["coefficients"].tolist(),
        "intercept": weights["intercept"],
        "last_event_hash": previous_event_hash
    }

    log_event("MODEL_SENT", payload)

    requests.post("http://127.0.0.1:5000/upload_model", json=payload)

def receive_and_verify_model(round_idx):
    res = requests.get("http://127.0.0.1:5000/get_global_model")
    if res.status_code != 200:
        print("[Client] ❌ No global model")
        return

    data = res.json()

    # Reverse verification
    included_clients = data.get("contributors", [])
    if client_id not in included_clients:
        print("[Client] ❌ Global model rejected (not included)")
        return

    model.load_weights({
        "coefficients": np.array(data["coefficients"]),
        "intercept": data["intercept"]
    })

    log_event("GLOBAL_MODEL_ACCEPTED", {
        "round": round_idx,
        "contributors": included_clients
    })

    print(f"[Client {client_id}] ✅ Global model verified & accepted")

# ---------------- MAIN LOOP ----------------
while training_counter < max_training_rounds:
    print(f"[Client {client_id}] 🏁 Round {training_counter + 1}")

    log_event("TRAINING_STARTED", {"round": training_counter + 1})

    batch_df = df.sample(n=ROW_BATCH_FOR_UPDATE, random_state=training_counter)
    X_batch = batch_df.iloc[:, :-1]
    y_batch = batch_df.iloc[:, -1]

    if len(set(y_batch)) < 2:
        print("[Client] ⚠️ Skipping round (single class)")
        continue

    X_batch_scaled = scaler.transform(X_batch.to_numpy(dtype=float))
    y_batch_np = y_batch.to_numpy(dtype=float)

    model.train(X_batch_scaled, y_batch_np)

    preds = model.predict(scaler.transform(X_test))
    preds_bin = (preds >= 0.5).astype(int)

    f1 = f1_score(y_test, preds_bin, average="weighted")
    acc = (preds_bin == y_test).mean()

    print(f"[Client {client_id}] 🎯 F1: {f1:.4f}, Acc: {acc:.4f}")

    log_event("TRAINING_COMPLETED", {
        "round": training_counter + 1,
        "f1": f1,
        "accuracy": acc
    })

    anchor_merkle_root(training_counter + 1)
    send_model_to_server(training_counter + 1)
    receive_and_verify_model(training_counter + 1)

    training_counter += 1
    time.sleep(3)

print(f"[Client {client_id}] ✅ Finished all rounds")
