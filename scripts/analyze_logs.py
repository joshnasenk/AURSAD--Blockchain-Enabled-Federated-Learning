import json
import os
import numpy as np

LOG_DIR = "data/aursad.csv"   # Change to your logs folder

accuracies = []
latencies = []

for fname in os.listdir(LOG_DIR):
    if fname.endswith(".json"):
        with open(os.path.join(LOG_DIR, fname), "r") as f:
            data = json.load(f)
            accuracies.append(data.get("accuracy", 0))
            latencies.append(data.get("latency", 0))

avg_acc = np.mean(accuracies) if accuracies else 0
avg_latency = np.mean(latencies) if latencies else 0

print(f"Avg Accuracy: {avg_acc*100:.2f}%")
print(f"Avg Latency: {avg_latency*1000:.2f} ms")
