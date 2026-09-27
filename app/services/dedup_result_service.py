from typing import Optional
from uuid import uuid4


# Temporary in-memory result storage
# Later, this can be replaced with a database.
_dedup_results: dict[str, dict] = {}


def save_dedup_result(result: dict) -> dict:
    """
    Save a deduplication result and generate a result ID.
    """

    result_id = f"dedup-{uuid4().hex[:12]}"

    saved_result = {
        "dedup_result_id": result_id,
        **result
    }

    _dedup_results[result_id] = saved_result

    return saved_result


def get_dedup_result(result_id: str) -> Optional[dict]:
    """
    Retrieve a deduplication result by its ID.
    """

    return _dedup_results.get(result_id)


def get_dedup_statistics() -> dict:
    """
    Return basic deduplication result statistics.
    """

    return {
        "total_results": len(_dedup_results)
    }