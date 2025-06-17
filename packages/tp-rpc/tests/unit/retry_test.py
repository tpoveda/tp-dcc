from __future__ import annotations

from unittest.mock import patch, MagicMock, call

import pytest
import Pyro5.errors

from tp.libs.rpc.core.retry import with_retry


def test_with_retry_success():
    """Test that a function succeeds on the first try."""

    mock_func = MagicMock(return_value=42)
    decorated = with_retry()(mock_func)

    result = decorated(1, 2, key="value")

    mock_func.assert_called_once_with(1, 2, key="value")
    assert result == 42


def test_with_retry_retry_then_success():
    """Test that a function retries after failure and then succeeds."""
    mock_func = MagicMock(
        side_effect=[Pyro5.errors.CommunicationError("Test error"), 42]
    )
    decorated = with_retry(max_attempts=3)(mock_func)

    with patch("time.sleep") as mock_sleep:
        result = decorated(1, 2, key="value")

        assert mock_func.call_count == 2
        mock_sleep.assert_called_once()
        assert result == 42


def test_with_retry_max_attempts_reached():
    """Test that a function fails after reaching max attempts."""

    mock_func = MagicMock(
        side_effect=Pyro5.errors.CommunicationError("Test error")
    )
    decorated = with_retry(max_attempts=3)(mock_func)

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(Pyro5.errors.CommunicationError):
            decorated(1, 2, key="value")

        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2


def test_with_retry_non_retryable_exception():
    """Test that a function doesn't retry for non-retryable exceptions."""

    mock_func = MagicMock(side_effect=ValueError("Test error"))
    decorated = with_retry(max_attempts=3)(mock_func)

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            decorated(1, 2, key="value")

        mock_func.assert_called_once_with(1, 2, key="value")
        mock_sleep.assert_not_called()


def test_with_retry_custom_exceptions():
    """Test that a function retries for custom exceptions."""

    mock_func = MagicMock(side_effect=[ValueError("Test error"), 42])
    decorated = with_retry(max_attempts=3, exceptions=(ValueError,))(mock_func)

    with patch("time.sleep") as mock_sleep:
        result = decorated(1, 2, key="value")

        assert mock_func.call_count == 2
        mock_sleep.assert_called_once()
        assert result == 42


def test_with_retry_backoff():
    """Test that retry backoff works correctly."""

    mock_func = MagicMock(
        side_effect=[
            Pyro5.errors.CommunicationError("Test error 1"),
            Pyro5.errors.CommunicationError("Test error 2"),
            42,
        ]
    )
    decorated = with_retry(
        max_attempts=4,
        initial_delay=1.0,
        backoff_factor=2.0,
        jitter=0.0,  # Disable jitter for predictable testing
    )(mock_func)

    with patch("time.sleep") as mock_sleep:
        result = decorated(1, 2, key="value")

        assert mock_func.call_count == 3
        # First delay should be 1.0, second should be 2.0
        mock_sleep.assert_has_calls([call(1.0), call(2.0)])
        assert result == 42
