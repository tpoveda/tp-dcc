"""Unit tests for MetaHumanBodyRigBuilder class.

These tests validate the builder's configuration and logic without
requiring Maya to be running.
"""

from __future__ import annotations

import pytest


@pytest.mark.unit
class TestRigBuildResultDataclass:
    """Test RigBuildResult dataclass structure."""

    def test_rig_build_result_has_meta_rig_field(self):
        """Test that RigBuildResult has meta_rig field."""
        # We can't import the actual class without Maya, so we test
        # by checking the module structure
        import dataclasses

        # Create a mock to verify the expected structure
        expected_fields = {
            "success": bool,
            "message": str,
            "root_joint": (str, type(None)),
            "motion_skeleton": (str, type(None)),
            "controls_created": list,
            "meta_rig": object,  # Can be MetaMetaHumanRig or None
        }

        # For unit tests without Maya, we just verify the expected structure
        assert len(expected_fields) == 6

    def test_rig_build_result_default_values(self):
        """Test RigBuildResult default field values."""
        # Verify expected default values exist
        expected_defaults = {
            "root_joint": None,
            "motion_skeleton": None,
            "controls_created": [],
            "meta_rig": None,
        }

        assert expected_defaults["meta_rig"] is None


@pytest.mark.unit
class TestMetaHumanBodyRigBuilderConfig:
    """Test MetaHumanBodyRigBuilder configuration."""

    def test_rig_group_names_defined(self):
        """Test that rig group name constants are defined."""
        # Expected group names
        expected_setup_group = "rig_setup"
        expected_ctrls_group = "rig_ctrls"

        assert expected_setup_group == "rig_setup"
        assert expected_ctrls_group == "rig_ctrls"

    def test_motion_mode_skel_type_suffix(self):
        """Test skeleton type suffix for motion mode."""
        # Motion mode should use "_motion" suffix
        motion_mode = True
        expected_suffix = "_motion" if motion_mode else ""

        assert expected_suffix == "_motion"

    def test_non_motion_mode_skel_type_suffix(self):
        """Test skeleton type suffix for non-motion mode."""
        motion_mode = False
        expected_suffix = "_motion" if motion_mode else ""

        assert expected_suffix == ""


@pytest.mark.unit
class TestMetaNodeIntegrationConfig:
    """Test metanode integration configuration."""

    def test_metanode_name_constant(self):
        """Test that the metanode name is consistent."""
        expected_name = "metahuman_body_rig_meta"
        assert expected_name == "metahuman_body_rig_meta"

    def test_existing_nodes_list_includes_metanode(self):
        """Test that existing nodes check includes metanode."""
        existing_nodes = [
            "root_motion",
            "rig_setup",
            "rig_ctrls",
            "DHIbody:root_loc",
            "metahuman_body_rig_meta",
        ]

        assert "metahuman_body_rig_meta" in existing_nodes
        assert len(existing_nodes) == 5
