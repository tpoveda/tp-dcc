from __future__ import annotations

import os
import zlib
import pickle
from typing import Any, Tuple

from loguru import logger


def compression_enabled() -> bool:
    """Check if compression is enabled via an environment variable.

    Returns:
        True if TP_DCC_RPC_ENABLE_COMPRESSION is "1".
    """
    return os.environ.get("TP_DCC_RPC_ENABLE_COMPRESSION", "0") == "1"


def get_compression_threshold() -> int:
    """Get the minimum size in bytes for data to be compressed.

    Returns:
        Threshold size in bytes.
    """

    try:
        return int(os.environ.get("TP_DCC_RPC_COMPRESSION_THRESHOLD", "10240"))
    except (ValueError, TypeError):
        return 10240  # Default: 10KB


def compress_data(data: Any) -> Tuple[bytes, bool]:
    """Compress serialized data if it exceeds the threshold.

    Args:
        data: The data to compress.

    Returns:
        Tuple of (compressed_data, is_compressed).
    """

    if not compression_enabled():
        return pickle.dumps(data), False

    serialized = pickle.dumps(data)
    threshold = get_compression_threshold()

    if len(serialized) < threshold:
        return serialized, False

    try:
        compressed = zlib.compress(serialized)
        compression_ratio = len(compressed) / len(serialized)
        logger.debug(
            f"Compressed {len(serialized)} bytes to "
            f"{len(compressed)} bytes (ratio: {compression_ratio:.2f})"
        )
        return compressed, True
    except Exception as e:
        logger.warning(f"[tp-rpc][compression] Compression failed: {e}")
        return serialized, False


def decompress_data(data: bytes, is_compressed: bool) -> Any:
    """Decompress and deserialize data.

    Args:
        data: The compressed or serialized data.
        is_compressed: Whether the data is compressed.

    Returns:
        The original data object.
    """

    if is_compressed:
        try:
            decompressed = zlib.decompress(data)
            return pickle.loads(decompressed)
        except Exception as e:
            logger.error(f"[tp-rpc][compression] Decompression failed: {e}")
            # Fall back to treating as uncompressed
            return pickle.loads(data)
    else:
        return pickle.loads(data)
