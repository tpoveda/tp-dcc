from __future__ import annotations

import os
import time
import pickle
import msgpack
from typing import Any

from loguru import logger

from .compression import compress_data, decompress_data


# Serialization formats
class SerializationFormat:
    """Enum-like class for serialization formats."""

    PICKLE = "pickle"
    MSGPACK = "msgpack"


def get_serialization_format() -> str:
    """Get the configured serialization format.

    Returns:
        Serialization format name.
    """
    return os.environ.get("TP_DCC_RPC_SERIALIZATION_FORMAT", SerializationFormat.PICKLE)


def serialize(data: Any) -> tuple[bytes, dict[str, Any]]:
    """Serialize data using the configured format with optional compression.

    Args:
        data: The data to serialize.

    Returns:
        Tuple of (serialized_data, metadata).
    """
    start_time = time.time()
    format_name = get_serialization_format()

    try:
        if format_name == SerializationFormat.MSGPACK:
            serialized = msgpack.packb(data, use_bin_type=True)
            is_compressed = False

            # Apply compression if enabled and beneficial.
            if len(serialized) > 1024:  # Only compress data > 1KB
                compressed, is_compressed = compress_data(serialized)
                if is_compressed:
                    serialized = compressed
        else:
            # Default to pickle with compression.
            serialized, is_compressed = compress_data(data)

        elapsed = time.time() - start_time
        metadata = {
            "format": format_name,
            "compressed": is_compressed,
            "size": len(serialized),
            "serialize_time": elapsed,
        }

        return serialized, metadata

    except Exception as e:
        logger.warning(
            f"[tp-rpc][serialization] Error with {format_name}: {e}. "
            f"Falling back to pickle."
        )
        # Fall back to pickle without compression.
        serialized = pickle.dumps(data)
        return serialized, {
            "format": SerializationFormat.PICKLE,
            "compressed": False,
            "size": len(serialized),
            "serialize_time": time.time() - start_time,
        }


def deserialize(data: bytes, metadata: dict[str, Any]) -> Any:
    """Deserialize data based on the provided metadata.

    Args:
        data: The serialized data.
        metadata: Serialization metadata.

    Returns:
        The deserialized data.
    """

    start_time = time.time()
    format_name = metadata.get("format", SerializationFormat.PICKLE)
    is_compressed = metadata.get("compressed", False)

    try:
        if format_name == SerializationFormat.MSGPACK:
            if is_compressed:
                decompressed = decompress_data(data, True)
                result = msgpack.unpackb(decompressed, raw=False)
            else:
                result = msgpack.unpackb(data, raw=False)
        else:
            # Default to pickle
            result = (
                decompress_data(data, is_compressed)
                if is_compressed
                else pickle.loads(data)
            )

        elapsed = time.time() - start_time
        logger.debug(
            f"[tp-rpc][serialization] Deserialized {len(data)} bytes "
            f"({format_name}, compressed={is_compressed}) in {elapsed:.6f}s"
        )
        return result

    except Exception as e:
        logger.error(f"[tp-rpc][serialization] Deserialization error: {e}")
        # Last resort fallback
        return pickle.loads(data)
