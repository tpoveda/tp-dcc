from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
import Pyro5.errors

from tp.libs.rpc.core.instances import (
    register_instance,
    unregister_instance,
    update_heartbeat,
    get_uri,
    list_instances,
    generate_and_register_instance_name,
    clear_dcc_instances,
    cleanup_registry,
)


@pytest.fixture
def mock_registry_file():
    """Mock registry file operations."""
    # Create a new registry for each test to avoid state leakage
    mock_registry = {
        "maya": {
            "maya-1": {
                "uri": "PYRO:rpc.service@localhost:9001",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            }
        },
        "unreal": {
            "unreal-1": {
                "uri": "PYRO:rpc.service@localhost:9002",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            }
        },
    }

    with patch(
        "tp.libs.rpc.core.instances._load_registry",
        return_value=mock_registry.copy(),
    ):
        with patch("tp.libs.rpc.core.instances._save_registry") as mock_save:
            yield mock_registry, mock_save


def test_register_instance(mock_registry_file):
    """Test registering a new instance."""
    mock_registry, mock_save = mock_registry_file

    result = register_instance(
        "blender", "PYRO:rpc.service@localhost:9003", "blender-1"
    )

    assert result == "blender-1"
    assert "blender" in mock_registry
    assert "blender-1" in mock_registry["blender"]
    assert (
        mock_registry["blender"]["blender-1"]["uri"]
        == "PYRO:rpc.service@localhost:9003"
    )
    mock_save.assert_called_once()


def test_register_instance_auto_name(mock_registry_file):
    """Test registering with auto-generated name."""
    mock_registry, mock_save = mock_registry_file

    result = register_instance("maya", "PYRO:rpc.service@localhost:9003")

    assert result == "maya-2"  # maya-1 already exists
    assert "maya-2" in mock_registry["maya"]
    mock_save.assert_called_once()


def test_unregister_instance(mock_registry_file):
    """Test unregistering an instance."""
    mock_registry, mock_save = mock_registry_file

    # Make a deep copy of the registry to ensure it's not modified by reference
    with patch(
        "tp.libs.rpc.core.instances._load_registry",
        return_value=mock_registry.copy(),
    ):
        unregister_instance("maya", "maya-1")

        # The key should still exist but be empty after unregistering the only instance
        assert "maya" in mock_registry
        assert "maya-1" not in mock_registry["maya"]
        mock_save.assert_called_once()


def test_unregister_last_instance(mock_registry_file):
    """Test unregistering the last instance of a DCC type."""
    mock_registry, mock_save = mock_registry_file

    unregister_instance("unreal", "unreal-1")

    assert "unreal" not in mock_registry
    mock_save.assert_called_once()


def test_update_heartbeat(mock_registry_file):
    """Test updating heartbeat."""
    mock_registry, mock_save = mock_registry_file

    # Store the old heartbeat
    old_heartbeat = mock_registry["maya"]["maya-1"]["last_heartbeat"]

    # Mock datetime.now to return a different time
    new_time = datetime.now(timezone.utc)
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = new_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        # Update the heartbeat
        update_heartbeat("maya", "maya-1")

        # The new heartbeat should be different
        assert (
            mock_registry["maya"]["maya-1"]["last_heartbeat"] != old_heartbeat
        )
        mock_save.assert_called_once()


def test_get_uri(mock_registry_file):
    """Test getting URI by DCC type and instance name."""
    mock_registry, _ = mock_registry_file

    uri = get_uri("maya", "maya-1")

    assert uri == "PYRO:rpc.service@localhost:9001"


def test_get_uri_default(mock_registry_file):
    """Test getting URI with default instance."""
    mock_registry, _ = mock_registry_file

    uri = get_uri("maya", None)

    assert uri == "PYRO:rpc.service@localhost:9001"


def test_get_uri_nonexistent(mock_registry_file):
    """Test getting URI for non-existent instance."""
    mock_registry, _ = mock_registry_file

    uri = get_uri("blender", "blender-1")

    assert uri is None


def test_list_instances(mock_registry_file):
    """Test listing all instances."""
    mock_registry, _ = mock_registry_file

    with patch("tp.libs.rpc.core.instances.cleanup_registry"):
        instances = list_instances()

        assert "maya" in instances
        assert "unreal" in instances
        assert "maya-1" in instances["maya"]
        assert "unreal-1" in instances["unreal"]


def test_list_instances_filtered(mock_registry_file):
    """Test listing instances filtered by DCC type."""
    mock_registry, _ = mock_registry_file

    with patch("tp.libs.rpc.core.instances.cleanup_registry"):
        instances = list_instances("maya")

        assert len(instances) == 1
        assert "maya" in instances
        assert "unreal" not in instances


def test_generate_and_register_instance_name(mock_registry_file):
    """Test generating and registering an instance name."""
    mock_registry, mock_save = mock_registry_file

    result = generate_and_register_instance_name(
        "maya", "PYRO:rpc.service@localhost:9003"
    )

    assert result == "maya-2"  # maya-1 already exists
    assert "maya-2" in mock_registry["maya"]
    mock_save.assert_called_once()


def test_clear_dcc_instances(mock_registry_file):
    """Test clearing all instances of a DCC type."""
    mock_registry, mock_save = mock_registry_file

    clear_dcc_instances("maya")

    assert "maya" not in mock_registry
    mock_save.assert_called_once()


def test_cleanup_registry(mock_registry_file):
    """Test cleaning up unreachable instances."""
    mock_registry, mock_save = mock_registry_file

    with patch("Pyro5.api.Proxy") as mock_proxy:
        # Make the first proxy reachable, second unreachable
        mock_instance1 = MagicMock()
        mock_instance2 = MagicMock()
        mock_instance2._pyroBind.side_effect = Pyro5.errors.CommunicationError(
            "Test error"
        )
        mock_proxy.side_effect = [mock_instance1, mock_instance2]

        removed = cleanup_registry()

        assert len(removed) == 1
        assert "unreal/unreal-1" in removed
        assert "maya" in mock_registry
        assert "unreal" not in mock_registry
        mock_save.assert_called_once()
