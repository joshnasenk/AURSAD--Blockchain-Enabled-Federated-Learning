from collections import defaultdict

# Initial trust score for all clients
trust_scores = defaultdict(lambda: 1.0)

# Configuration
MAX_TRUST = 2.0
MIN_TRUST = 0.1
TRUST_STEP_UP = 0.05
TRUST_STEP_DOWN = 0.1


def update_trust(client_id, success=True):
    """
    Update trust score based on event consistency.
    """
    current = trust_scores[client_id]

    if success:
        current += TRUST_STEP_UP
    else:
        current -= TRUST_STEP_DOWN

    # Clamp trust
    current = max(MIN_TRUST, min(MAX_TRUST, current))
    trust_scores[client_id] = current

    return current
