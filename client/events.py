import hashlib
import json
import time


def hash_event(event_dict):
    """
    Deterministically hash an event dictionary.
    """
    event_string = json.dumps(event_dict, sort_keys=True)
    return hashlib.sha256(event_string.encode()).hexdigest()


def create_event(event_type, client_id, payload, prev_hash):
    """
    Create a lifecycle event with causal linkage.
    """
    event = {
        "event_type": event_type,
        "client_id": client_id,
        "timestamp": time.time(),
        "payload": payload,
        "prev_event_hash": prev_hash
    }

    event_hash = hash_event(event)
    event["event_hash"] = event_hash

    return event
