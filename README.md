# Event-Driven Federated Learning with Trust-Weighted Aggregation and Blockchain Anchoring

## Overview

This repository implements a **secure, event-driven federated learning (FL) framework** designed for distributed and industrial IoT environments.
The system introduces **verifiable lifecycle governance** into federated learning by combining:

* event-level provenance,
* cryptographic hash chaining,
* Merkle root anchoring on blockchain, and
* trust-weighted aggregation.

Unlike conventional approaches that focus on verifying *model artifacts* or *data updates*, this framework verifies the **entire causal sequence of training actions** that lead to a global model.

The result is a federated learning system where **process integrity**, not just performance metrics, governs participation and influence.

---

## Key Contributions

This work introduces the following architectural extensions to standard federated learning:

### 1. Event Abstraction Layer

Training actions are modeled as first-class events rather than implicit side effects.

Each client explicitly records events such as:

* training start and completion,
* model update transmission,
* global model acceptance.

Every event includes:

* event type,
* round identifier,
* client identifier,
* timestamp,
* cryptographic reference to the previous event.

This allows the learning process itself to be audited.

---

### 2. Client-Side Event Hash Chain

Each client maintains a **locally chained event log**:

```
E₁ → E₂ → E₃ → … → Eₙ
```

Any missing, reordered, or tampered event becomes detectable through hash inconsistency.

This enforces **causal ordering** of learning actions.

---

### 3. Merkle Root Anchoring per Federated Round

To ensure scalability, full event logs remain off-chain.

For each training round:

* a Merkle tree is constructed from event hashes,
* only the Merkle root is anchored on-chain.

This provides tamper-evident proof of the learning process without blockchain storage overhead.

---

### 4. Server-Side Pre-Aggregation Verification

Before aggregation, the server verifies:

* event chain continuity,
* round consistency,
* client participation validity.

Updates that fail verification are excluded **before** aggregation.

This shifts trust enforcement from post-hoc evaluation to **pre-aggregation governance**.

---

### 5. Bidirectional (Reverse) Verification

**Key Novelty**

After aggregation, the server returns:

* the global model,
* contributor metadata,
* aggregation proof.

Each client verifies:

* its inclusion in the aggregation,
* consistency with its anchored event history.

Clients reject global models that fail verification, making the **aggregator accountable**.

---

### 6. Trust Scoring from Event Consistency

Client trust is derived from **process integrity**, not accuracy or loss.

Trust scores are updated based on:

* valid event chains,
* correct timing,
* successful reverse verification.

This avoids bias toward high-performing but potentially malicious nodes.

---

### 7. Trust-Weighted Aggregation

Aggregation is performed as:

```
GlobalModel = Σ (trustᵢ × updateᵢ) / Σ trustᵢ
```

Nodes with inconsistent behavior naturally lose influence without hard exclusion.

---

## System Architecture

* **Clients**

  * Train local models
  * Record event chains
  * Anchor Merkle roots on blockchain
  * Verify global models

* **Server**

  * Validates client event proofs
  * Computes trust scores
  * Performs trust-weighted aggregation

* **Blockchain Layer**

  * Stores Merkle roots per round
  * Provides immutable audit trail

---

## Repository Structure

```
client/
  ├── client.py          # FL client with event logging & verification
  ├── events.py          # Event abstraction & hashing
  ├── merkle.py          # Merkle tree utilities
  └── model.py           # Local ML model

server/
  ├── server.py          # Aggregation & verification logic
  ├── trust.py           # Trust scoring mechanism

contracts/
  └── DataVerification.sol  # On-chain anchoring contract

models/
  └── ml_model.py        # Shared ML model definition

scripts/
  ├── deploy.js          # Smart contract deployment
  └── analysis utilities
```

---

## Execution Flow (High Level)

1. Clients train locally and record training events.
2. Event chains are hashed and summarized via Merkle roots.
3. Merkle roots are anchored on blockchain.
4. Clients submit model updates with event proofs.
5. Server verifies event integrity and computes trust.
6. Trust-weighted aggregation is performed.
7. Global model is returned with aggregation proof.
8. Clients verify inclusion before accepting the model.

---

## Intended Use

This framework is designed for:

* industrial IoT deployments,
* multi-stakeholder federated learning,
* security-critical distributed systems,
* research on trustworthy machine learning infrastructure.

It is **architecture-oriented**, not application-specific.

---

## Research & IP Status

This repository represents an active research prototype.
The architecture emphasizes **verifiable governance of the federated learning lifecycle**, rather than model-specific optimizations.

Further work includes:

* hardware deployment on edge devices (e.g., Raspberry Pi),
* scalability evaluation,
* formal security analysis,
* patent and publication preparation.

---

## Disclaimer

This codebase is provided for research and experimental purposes.
It is not intended for production deployment without further hardening and evaluation.

---

