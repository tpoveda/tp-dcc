from __future__ import annotations

import os
import time
import pickle
import msgpack
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.core.serialization import (
    SerializationFormat,
    get_serialization_format,
    serialize,
    deserialize,
)


def test_get_serialization_format():
    # Test with msgpack
    with patch.dict(os.environ, {"TP_DCC_RPC_SERIALIZATION_FORMAT": "msgpack"}):
        assert get_serialization_format() == "msgpack"

    # Test with pickle
    with patch.dict(os.environ, {"TP_DCC_RPC_SERIALIZATION_FORMAT": "pickle"}):
        assert get_serialization_format() == "pickle"

    # Test default value
    with patch.dict(os.environ, {}, clear=True):
        assert get_serialization_format() == "pickle"


def test_serialize_pickle():
    # Test serialization with pickle format
    with patch(
        "tp.libs.rpc.core.serialization.get_serialization_format",
        return_value="pickle",
    ):
        with patch(
            "tp.libs.rpc.core.serialization.compress_data",
            return_value=(b"compressed_data", True),
        ):
            test_data = {"test": "data"}
            result, metadata = serialize(test_data)

            assert result == b"compressed_data"
            assert metadata["format"] == "pickle"
            assert metadata["compressed"] is True
            assert metadata["size"] == len(result)
            assert "serialize_time" in metadata


def test_serialize_msgpack():
    # Test serialization with msgpack format
    with patch(
        "tp.libs.rpc.core.serialization.get_serialization_format",
        return_value="msgpack",
    ):
        # Mock msgpack.packb to return a predictable value
        with patch("msgpack.packb", return_value=b"msgpack_data"):
            # Small data that won't trigger compression
            with patch(
                "tp.libs.rpc.core.serialization.compress_data",
                return_value=(b"compressed_data", True),
            ):
                test_data = {"test": "data"}
                result, metadata = serialize(test_data)

                assert metadata["format"] == "msgpack"
                assert "serialize_time" in metadata


def test_serialize_msgpack_with_compression():
    # Test msgpack serialization with compression for large data
    with patch(
        "tp.libs.rpc.core.serialization.get_serialization_format",
        return_value="msgpack",
    ):
        # Mock msgpack.packb to return data large enough to trigger compression
        with patch("msgpack.packb", return_value=b"x" * 2000):
            with patch(
                "tp.libs.rpc.core.serialization.compress_data",
                return_value=(b"compressed_data", True),
            ):
                test_data = {"test": "data" * 100}
                result, metadata = serialize(test_data)

                assert result == b"compressed_data"
                assert metadata["format"] == "msgpack"
                assert metadata["compressed"] is True


def test_serialize_error():
    # Test error handling during serialization
    with patch(
        "tp.libs.rpc.core.serialization.get_serialization_format",
        return_value="msgpack",
    ):
        with patch("msgpack.packb", side_effect=Exception("Test error")):
            with patch("loguru.logger.warning") as mock_logger:
                test_data = {"test": "data"}
                result, metadata = serialize(test_data)

                assert metadata["format"] == "pickle"
                assert metadata["compressed"] is False
                mock_logger.assert_called_once()


def test_deserialize_pickle():
    # Test deserialization with pickle format
    test_data = {"test": "data"}
    serialized = pickle.dumps(test_data)
    metadata = {"format": "pickle", "compressed": False}

    result = deserialize(serialized, metadata)
    assert result == test_data


def test_deserialize_pickle_compressed():
    # Test deserialization with compressed pickle data
    with patch(
        "tp.libs.rpc.core.serialization.decompress_data",
        return_value={"test": "data"},
    ):
        metadata = {"format": "pickle", "compressed": True}

        result = deserialize(b"compressed_data", metadata)
        assert result == {"test": "data"}


def test_deserialize_msgpack():
    # Test deserialization with msgpack format
    with patch("msgpack.unpackb", return_value={"test": "data"}):
        metadata = {"format": "msgpack", "compressed": False}

        result = deserialize(b"msgpack_data", metadata)
        assert result == {"test": "data"}


def test_deserialize_msgpack_compressed():
    # Test deserialization with compressed msgpack data
    with patch(
        "tp.libs.rpc.core.serialization.decompress_data",
        return_value=b"decompressed_data",
    ):
        with patch("msgpack.unpackb", return_value={"test": "data"}):
            metadata = {"format": "msgpack", "compressed": True}

            result = deserialize(b"compressed_data", metadata)
            assert result == {"test": "data"}


def test_deserialize_error():
    # Test error handling during deserialization
    with patch(
        "tp.libs.rpc.core.serialization.decompress_data",
        side_effect=Exception("Test error"),
    ):
        with patch("loguru.logger.error") as mock_logger:
            with patch("pickle.loads", return_value={"test": "data"}):
                metadata = {"format": "pickle", "compressed": True}

                result = deserialize(b"data", metadata)
                assert result == {"test": "data"}
                mock_logger.assert_called_once()
