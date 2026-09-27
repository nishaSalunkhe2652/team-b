from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.chunking_service import process_file
from app.services.deduplication import compute_dedup
from app.services.integrity_service import build_merkle_root

from app.services.hash_index_service import (
    add_chunk,
    find_chunk,
    get_index_statistics
)

from app.services.dedup_result_service import (
    save_dedup_result,
    get_dedup_result
)

from app.services.storage_service import (
    store_chunk,
    get_chunk,
    get_storage_statistics
)


app = FastAPI(
    title="APNILEAP Team B Processing Backend",
    version="1.0.0"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChunkProcessRequest(BaseModel):
    file_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    chunk_size: int = Field(default=1024 * 1024, gt=0)
    hash_algorithm: str = "sha256"


class DedupRequest(BaseModel):
    file_id: str = Field(min_length=1)
    chunk_version: str = "v1"
    hash_algorithm: str = "sha256"
    chunks: list[dict] = Field(min_length=1)


class IntegrityVerifyRequest(BaseModel):
    chunk_hashes: list[str] = Field(min_length=1)
    expected_merkle_root: str | None = None


class HashIndexRequest(BaseModel):
    chunk_hash: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    size: int = Field(gt=0)


class ProcessFileRequest(BaseModel):
    file_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    chunk_size: int = Field(default=1024 * 1024, gt=0)
    hash_algorithm: str = "sha256"
    version: str = "v1"


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "team-b",
        "version": "v1"
    }


# ============================================================
# CHUNK PROCESSING
# ============================================================

@app.post("/api/v1/chunks/process")
def process_chunks(request: ChunkProcessRequest):

    try:

        result = process_file(
            file_path=request.file_path,
            chunk_size=request.chunk_size,
            hash_algorithm=request.hash_algorithm
        )

        chunks = result["chunks"]

        new_chunks_indexed = 0
        existing_chunks = 0

        for chunk in chunks:

            existing = find_chunk(chunk["hash"])

            if existing:

                existing_chunks += 1

            else:

                add_chunk(
                    chunk_hash=chunk["hash"],
                    chunk_id=chunk["chunk_id"],
                    size=chunk["size"]
                )

                new_chunks_indexed += 1

        return {
            "data": {
                "file_id": request.file_id,
                "chunk_version": "v1",
                "file_size": result["file_size"],
                "chunk_size": result["chunk_size"],
                "hash_algorithm": result["hash_algorithm"],
                "total_chunks": result["total_chunks"],
                "chunks": result["chunks"],
                "hash_index": {
                    "new_chunks_indexed": new_chunks_indexed,
                    "existing_chunks": existing_chunks
                }
            },
            "meta": {
                "api_version": "v1"
            }
        }

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ============================================================
# DEDUPLICATION
# ============================================================

@app.post("/api/v1/dedup/compute")
def compute_deduplication(request: DedupRequest):

    try:

        result = compute_dedup(
            request.chunks
        )

        saved_result = save_dedup_result({
            "file_id": request.file_id,
            "chunk_version": request.chunk_version,
            "hash_algorithm": request.hash_algorithm,
            "total_chunks": len(request.chunks),
            **result
        })

        return {
            "data": saved_result,
            "meta": {
                "api_version": "v1"
            }
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ============================================================
# GET DEDUPLICATION RESULT
# ============================================================

@app.get("/api/v1/dedup/{result_id}")
def get_dedup_result_by_id(result_id: str):

    result = get_dedup_result(
        result_id
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Deduplication result not found"
        )

    return {
        "data": result,
        "meta": {
            "api_version": "v1"
        }
    }


# ============================================================
# INTEGRITY VERIFICATION
# ============================================================

@app.post("/api/v1/integrity/verify")
def verify_integrity(
    request: IntegrityVerifyRequest
):

    calculated_merkle_root = build_merkle_root(
        request.chunk_hashes
    )

    expected_root = request.expected_merkle_root

    if expected_root is None:

        verification_status = "ROOT_CALCULATED"
        corrupted_chunks = 0
        verified_chunks = len(
            request.chunk_hashes
        )

    elif calculated_merkle_root == expected_root:

        verification_status = "VERIFIED"
        corrupted_chunks = 0
        verified_chunks = len(
            request.chunk_hashes
        )

    else:

        verification_status = "CORRUPTED"
        corrupted_chunks = len(
            request.chunk_hashes
        )
        verified_chunks = 0

    return {
        "data": {
            "merkle_root": calculated_merkle_root,
            "expected_merkle_root": expected_root,
            "verified_chunks": verified_chunks,
            "corrupted_chunks": corrupted_chunks,
            "verification_status": verification_status
        },
        "meta": {
            "api_version": "v1"
        }
    }


# ============================================================
# HASH INDEX - ADD
# ============================================================

@app.post("/internal/v1/hash-index/add")
def add_hash_index(
    request: HashIndexRequest
):

    result = add_chunk(
        chunk_hash=request.chunk_hash,
        chunk_id=request.chunk_id,
        size=request.size
    )

    return {
        "data": result,
        "meta": {
            "api_version": "v1"
        }
    }


# ============================================================
# HASH INDEX - FIND
# ============================================================

@app.get("/internal/v1/hash-index/{chunk_hash}")
def get_hash_index(
    chunk_hash: str
):

    result = find_chunk(
        chunk_hash
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Chunk hash not found"
        )

    return {
        "data": result,
        "meta": {
            "api_version": "v1"
        }
    }


# ============================================================
# HASH INDEX - STATISTICS
# ============================================================

@app.get("/api/v1/chunks/index")
def get_chunk_index():

    result = get_index_statistics()

    return {
        "data": result,
        "meta": {
            "api_version": "v1"
        }
    }


# ============================================================
# STORAGE - STATISTICS
# ============================================================

@app.get("/api/v1/storage/stats")
def get_storage_stats():

    result = get_storage_statistics()

    return {
        "data": result,
        "meta": {
            "api_version": "v1"
        }
    }


# ============================================================
# STORAGE - FIND CHUNK
# ============================================================

@app.get("/api/v1/storage/{chunk_hash}")
def get_stored_chunk(
    chunk_hash: str
):

    result = get_chunk(
        chunk_hash
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Stored chunk not found"
        )

    return {
        "data": result,
        "meta": {
            "api_version": "v1"
        }
    }


# ============================================================
# END-TO-END FILE PROCESSING
# ============================================================

@app.post("/api/v1/process")
def process_file_end_to_end(
    request: ProcessFileRequest
):

    try:

        # ----------------------------------------------------
        # 1. READ FILE + CHUNK + HASH
        # ----------------------------------------------------

        chunk_result = process_file(
            file_path=request.file_path,
            chunk_size=request.chunk_size,
            hash_algorithm=request.hash_algorithm
        )

        chunks = chunk_result["chunks"]


        # ----------------------------------------------------
        # 2. HASH INDEX + ACTUAL CHUNK STORAGE
        # ----------------------------------------------------

        new_chunks_indexed = 0
        existing_chunks = 0

        newly_stored_chunks = 0
        reused_chunks = 0
        storage_bytes_saved = 0

        for chunk in chunks:

            chunk_hash = chunk["hash"]
            chunk_id = chunk["chunk_id"]
            chunk_size = chunk["size"]


            # -----------------------------------------------
            # Check hash index
            # -----------------------------------------------

            existing = find_chunk(
                chunk_hash
            )

            if existing:

                existing_chunks += 1

            else:

                add_chunk(
                    chunk_hash=chunk_hash,
                    chunk_id=chunk_id,
                    size=chunk_size
                )

                new_chunks_indexed += 1


            # -----------------------------------------------
            # Store chunk only once
            # -----------------------------------------------

            storage_result = store_chunk(
                chunk_hash=chunk_hash,
                chunk_id=chunk_id,
                size=chunk_size
            )

            if storage_result["stored"]:

                newly_stored_chunks += 1

            else:

                reused_chunks += 1

                storage_bytes_saved += chunk_size


        # ----------------------------------------------------
        # 3. DEDUPLICATION CALCULATION
        # ----------------------------------------------------

        dedup_result = compute_dedup(
            chunks
        )


        # ----------------------------------------------------
        # 4. COLLECT CHUNK HASHES
        # ----------------------------------------------------

        chunk_hashes = [
            chunk["hash"]
            for chunk in chunks
        ]


        # ----------------------------------------------------
        # 5. CALCULATE MERKLE ROOT
        # ----------------------------------------------------

        merkle_root = build_merkle_root(
            chunk_hashes
        )


        # ----------------------------------------------------
        # 6. RETURN COMPLETE RESULT
        # ----------------------------------------------------

        return {
            "data": {

                "file_id": request.file_id,

                "version": request.version,

                "file_size": chunk_result[
                    "file_size"
                ],

                "chunk_size": chunk_result[
                    "chunk_size"
                ],

                "hash_algorithm": chunk_result[
                    "hash_algorithm"
                ],

                "total_chunks": chunk_result[
                    "total_chunks"
                ],

                "chunks": chunks,


                # -------------------------------------------
                # HASH INDEX
                # -------------------------------------------

                "hash_index": {

                    "new_chunks_indexed":
                        new_chunks_indexed,

                    "existing_chunks":
                        existing_chunks
                },


                # -------------------------------------------
                # STORAGE
                # -------------------------------------------

                "storage": {

                    "new_chunks_stored":
                        newly_stored_chunks,

                    "reused_chunks":
                        reused_chunks,

                    "storage_bytes_saved":
                        storage_bytes_saved
                },


                # -------------------------------------------
                # DEDUPLICATION
                # -------------------------------------------

                "deduplication": {

                    "original_size":
                        dedup_result[
                            "original_size"
                        ],

                    "unique_storage_size":
                        dedup_result[
                            "unique_storage_size"
                        ],

                    "duplicate_storage_avoided":
                        dedup_result[
                            "duplicate_storage_avoided"
                        ],

                    "unique_chunks":
                        dedup_result[
                            "unique_chunks"
                        ],

                    "duplicate_chunks":
                        dedup_result[
                            "duplicate_chunks"
                        ],

                    "storage_ratio":
                        dedup_result[
                            "storage_ratio"
                        ],

                    "savings_ratio":
                        dedup_result[
                            "savings_ratio"
                        ]
                },


                # -------------------------------------------
                # INTEGRITY
                # -------------------------------------------

                "integrity": {

                    "merkle_root":
                        merkle_root,

                    "verified_chunks":
                        len(chunk_hashes),

                    "corrupted_chunks":
                        0,

                    "verification_status":
                        "ROOT_CALCULATED"
                }
            },

            "meta": {
                "api_version": "v1"
            }
        }


    except FileNotFoundError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )