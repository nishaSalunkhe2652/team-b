
import hashlib
from pathlib import Path


def process_file(
    file_path: str,
    chunk_size: int = 1024 * 1024,
    hash_algorithm: str = "sha256"
):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if hash_algorithm.lower() != "sha256":
        raise ValueError("Only sha256 is supported currently")

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    chunks = []
    chunk_index = 0
    total_size = 0

    with path.open("rb") as file:
        while True:
            chunk_data = file.read(chunk_size)

            if not chunk_data:
                break

            chunk_hash = hashlib.sha256(
                chunk_data
            ).hexdigest()

            chunks.append({
                "chunk_id": f"chunk-{chunk_index + 1:04d}",
                "chunk_index": chunk_index,
                "size": len(chunk_data),
                "hash": chunk_hash
            })

            total_size += len(chunk_data)
            chunk_index += 1

    return {
        "file_size": total_size,
        "chunk_size": chunk_size,
        "hash_algorithm": hash_algorithm,
        "total_chunks": len(chunks),
        "chunks": chunks
    }
