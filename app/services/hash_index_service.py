
from typing import Optional


# Temporary in-memory hash index.
# Later, this can be replaced with a database or persistent storage.
_hash_index: dict[str, dict] = {}


def add_chunk(
    chunk_hash: str,
    chunk_id: str,
    size: int
) -> dict:
    """
    Add a chunk to the hash index if it does not already exist.
    """

    if chunk_hash in _hash_index:
        return {
            "created": False,
            "existing_chunk": _hash_index[chunk_hash]
        }

    chunk_record = {
        "chunk_id": chunk_id,
        "hash": chunk_hash,
        "size": size
    }

    _hash_index[chunk_hash] = chunk_record

    return {
        "created": True,
        "existing_chunk": chunk_record
    }


def find_chunk(chunk_hash: str) -> Optional[dict]:
    """
    Find a chunk by its hash.
    """

    return _hash_index.get(chunk_hash)


def get_index_statistics() -> dict:
    """
    Return basic hash index statistics.
    """

    return {
        "total_indexed_chunks": len(_hash_index)
    }
