import time
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
import os

# Parameters
NUM_CLIENTS = 4
NUM_ROUNDS = 100

# Simulate dataset (you can increase samples/features for harder challenge)
X, y = make_classification(n_samples=2000, n_features=25, n_informative=18,
                           n_classes=2, random_state=42)

X_clients = np.array_split(X, NUM_CLIENTS)
y_clients = np.array_split(y, NUM_CLIENTS)

# Global test set
X_train_all, X_test, y_train_all, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

# Create folders (optional)
os.makedirs("saved_models", exist_ok=True)
os.makedirs("server_models", exist_ok=True)

# Initialize global model with smaller learning rate for smoother convergence
global_model = SGDClassifier(loss='log_loss', max_iter=1000, tol=1e-4,
                             learning_rate='optimal', eta0=0.01,
                             random_state=42)

# Initialize model with partial_fit on first client data
global_model.partial_fit(X_clients[0], y_clients[0], classes=np.unique(y))

round_accuracies = []
round_times = []

for round_num in range(NUM_ROUNDS):
    start_time = time.time()

    for i in range(NUM_CLIENTS):
        global_model.partial_fit(X_clients[i], y_clients[i])

    round_time = time.time() - start_time

    y_pred = global_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    round_accuracies.append(acc)
    round_times.append(round_time)

    if (round_num + 1) % 10 == 0 or round_num == 0:
        print(f"Round {round_num + 1}: Accuracy = {acc:.4f}, Time = {round_time:.4f} sec")

# Plot results
fig, ax = plt.subplots(1, 2, figsize=(14, 6))

ax[0].plot(range(1, NUM_ROUNDS + 1), round_accuracies, marker='o', color='purple')
ax[0].set_title('Global Model Accuracy per Round')
ax[0].set_xlabel('Round')
ax[0].set_ylabel('Accuracy')
ax[0].grid(True)

ax[1].plot(range(1, NUM_ROUNDS + 1), round_times, marker='o', color='orange')
ax[1].set_title('Time Taken per Round')
ax[1].set_xlabel('Round')
ax[1].set_ylabel('Time (seconds)')
ax[1].grid(True)

plt.tight_layout()
plt.show()
