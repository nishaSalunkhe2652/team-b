import hashlib


def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def build_merkle_root(hashes: list[str]) -> str:
    if not hashes:
        return ""

    current_level = hashes[:]

    while len(current_level) > 1:
        next_level = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]

            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                right = left

            combined = left + right
            parent_hash = hashlib.sha256(
                combined.encode()
            ).hexdigest()

            next_level.append(parent_hash)

        current_level = next_level

    return current_level[0]