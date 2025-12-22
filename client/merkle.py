import hashlib


def _hash_pair(a, b):
    return hashlib.sha256((a + b).encode()).hexdigest()


def merkle_root(hash_list):
    """
    Compute Merkle root from a list of hashes.
    """
    if not hash_list:
        return hashlib.sha256(b"EMPTY").hexdigest()

    current_level = hash_list[:]

    while len(current_level) > 1:
        next_level = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            next_level.append(_hash_pair(left, right))

        current_level = next_level

    return current_level[0]
