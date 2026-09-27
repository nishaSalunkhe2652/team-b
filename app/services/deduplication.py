
def compute_dedup(chunks: list):
    seen_hashes = set()

    unique_chunks = 0
    duplicate_chunks = 0
    unique_storage_size = 0
    duplicate_storage_avoided = 0

    for chunk in chunks:
        chunk_hash = chunk["hash"]
        chunk_size = chunk["size"]

        if chunk_hash in seen_hashes:
            duplicate_chunks += 1
            duplicate_storage_avoided += chunk_size
        else:
            seen_hashes.add(chunk_hash)
            unique_chunks += 1
            unique_storage_size += chunk_size

    original_size = sum(
        chunk["size"] for chunk in chunks
    )

    if original_size > 0:
        storage_ratio = unique_storage_size / original_size
        savings_ratio = (
            duplicate_storage_avoided / original_size
        ) * 100
    else:
        storage_ratio = 0
        savings_ratio = 0

    return {
        "original_size": original_size,
        "unique_storage_size": unique_storage_size,
        "duplicate_storage_avoided": duplicate_storage_avoided,
        "unique_chunks": unique_chunks,
        "duplicate_chunks": duplicate_chunks,
        "storage_ratio": round(storage_ratio, 4),
        "savings_ratio": round(savings_ratio, 2)
    }
