from pathlib import Path


# Simple in-memory chunk storage
# Key   = chunk hash
# Value = chunk information

_chunk_storage: dict[str, dict] = {}


def store_chunk(
    chunk_hash: str,
    chunk_id: str,
    size: int
):
    """
    Store a chunk only if its hash does not already exist.
    """

    if chunk_hash in _chunk_storage:

        return {
            "stored": False,
            "already_exists": True,
            "chunk_hash": chunk_hash,
            "chunk_id": _chunk_storage[chunk_hash]["chunk_id"],
            "size": _chunk_storage[chunk_hash]["size"]
        }

    _chunk_storage[chunk_hash] = {
        "chunk_id": chunk_id,
        "size": size
    }

    return {
        "stored": True,
        "already_exists": False,
        "chunk_hash": chunk_hash,
        "chunk_id": chunk_id,
        "size": size
    }


def get_chunk(chunk_hash: str):
    """
    Find a stored chunk using its hash.
    """

    return _chunk_storage.get(chunk_hash)


def get_storage_statistics():
    """
    Return basic storage statistics.
    """

    total_chunks = len(_chunk_storage)

    total_size = sum(
        chunk["size"]
        for chunk in _chunk_storage.values()
    )

    return {
        "total_stored_chunks": total_chunks,
        "total_stored_size": total_size
    }