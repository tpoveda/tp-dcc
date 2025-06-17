from __future__ import annotations

import os
import pickle
import zlib
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.core.compression import (
    compression_enabled,
    get_compression_threshold,
    compress_data,
    decompress_data,
)


def test_compression_enabled():
    # Test when enabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ENABLE_COMPRESSION": "1"}):
        assert compression_enabled() is True

    # Test when disabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ENABLE_COMPRESSION": "0"}):
        assert compression_enabled() is False

    # Test default value
    with patch.dict(os.environ, {}, clear=True):
        assert compression_enabled() is False


def test_get_compression_threshold():
    # Test with valid value
    with patch.dict(os.environ, {"TP_DCC_RPC_COMPRESSION_THRESHOLD": "5000"}):
        assert get_compression_threshold() == 5000

    # Test with invalid value
    with patch.dict(os.environ, {"TP_DCC_RPC_COMPRESSION_THRESHOLD": "invalid"}):
        assert get_compression_threshold() == 10240

    # Test default value
    with patch.dict(os.environ, {}, clear=True):
        assert get_compression_threshold() == 10240


def test_compress_data_disabled():
    # Test when compression is disabled
    with patch(
        "tp.libs.rpc.core.compression.compression_enabled", return_value=False
    ):
        test_data = {"test": "data"}
        result, is_compressed = compress_data(test_data)

        assert is_compressed is False
        assert pickle.loads(result) == test_data


def test_compress_data_below_threshold():
    # Test when data size is below threshold
    with patch(
        "tp.libs.rpc.core.compression.compression_enabled", return_value=True
    ):
        with patch(
            "tp.libs.rpc.core.compression.get_compression_threshold",
            return_value=10000,
        ):
            test_data = {"test": "data"}  # Small data
            result, is_compressed = compress_data(test_data)

            assert is_compressed is False
            assert pickle.loads(result) == test_data


def test_compress_data_above_threshold():
    # Test when data size is above threshold
    with patch(
        "tp.libs.rpc.core.compression.compression_enabled", return_value=True
    ):
        with patch(
            "tp.libs.rpc.core.compression.get_compression_threshold",
            return_value=10,
        ):
            # Create data large enough to trigger compression
            test_data = {"test": "data" * 100}
            result, is_compressed = compress_data(test_data)

            assert is_compressed is True
            # Verify we can decompress it
            decompressed = zlib.decompress(result)
            assert pickle.loads(decompressed) == test_data


def test_compress_data_error():
    # Test when compression raises an error
    with patch(
        "tp.libs.rpc.core.compression.compression_enabled", return_value=True
    ):
        with patch(
            "tp.libs.rpc.core.compression.get_compression_threshold",
            return_value=10,
        ):
            with patch("zlib.compress", side_effect=Exception("Test error")):
                with patch("loguru.logger.warning") as mock_logger:
                    test_data = {"test": "data" * 100}
                    result, is_compressed = compress_data(test_data)

                    assert is_compressed is False
                    assert pickle.loads(result) == test_data
                    mock_logger.assert_called_once()


def test_decompress_data_not_compressed():
    # Test when data is not compressed
    test_data = {"test": "data"}
    serialized = pickle.dumps(test_data)
    result = decompress_data(serialized, False)

    assert result == test_data


def test_decompress_data_compressed():
    # Test when data is compressed
    test_data = {"test": "data"}
    serialized = pickle.dumps(test_data)
    compressed = zlib.compress(serialized)
    result = decompress_data(compressed, True)

    assert result == test_data


def test_decompress_data_error():
    # Test when decompression raises an error
    with patch("zlib.decompress", side_effect=Exception("Test error")):
        with patch("loguru.logger.error") as mock_logger:
            test_data = {"test": "data"}
            serialized = pickle.dumps(test_data)
            # This isn't actually compressed, but we tell it that it is
            result = decompress_data(serialized, True)

            assert result == test_data
            mock_logger.assert_called_once()
