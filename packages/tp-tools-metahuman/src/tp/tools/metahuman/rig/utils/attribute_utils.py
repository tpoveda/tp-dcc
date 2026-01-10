"""Attribute utility functions for Maya rig building.

This module provides utility functions for managing Maya node attributes.
Uses tp.libs.maya.wrapper for OpenMaya 2.0 operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

import maya.cmds as cmds
from maya.api import OpenMaya as om2

# Import wrapper module for OpenMaya operations
from tp.libs.maya import wrapper
from tp.libs.maya.om import attributetypes

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions using Wrapper
# ============================================================================


def get_node(node_name: str) -> Optional[wrapper.DGNode]:
    """Get a wrapper node from node name.

    Args:
        node_name: Name of the Maya node.

    Returns:
        Wrapper DGNode/DagNode or None if not found.
    """
    try:
        return wrapper.node_by_name(node_name)
    except (RuntimeError, ValueError):
        return None


def get_plug(node_name: str, attr_name: str) -> Optional[wrapper.Plug]:
    """Get a Plug wrapper for a node attribute.

    Args:
        node_name: Name of the node.
        attr_name: Name of the attribute.

    Returns:
        Plug wrapper or None if not found.
    """
    node = get_node(node_name)
    if node:
        try:
            return node.attribute(attr_name)
        except (RuntimeError, KeyError):
            return None
    return None


def node_exists(node_name: str) -> bool:
    """Check if a node exists using wrapper.

    Args:
        node_name: Name of the node.

    Returns:
        True if node exists.
    """
    node = get_node(node_name)
    return node is not None and node.exists()


# ============================================================================
# Attribute Configuration Dataclasses
# ============================================================================


@dataclass
class AttributeSettings:
    """Settings for attribute visibility, keyability, and locking."""

    keyable: bool = True
    visible: bool = True
    locked: bool = False


@dataclass
class TransformAttributeConfig:
    """Configuration for transform attribute cleanup."""

    translate: AttributeSettings = None
    rotate: AttributeSettings = None
    scale: AttributeSettings = None

    def __post_init__(self):
        if self.translate is None:
            self.translate = AttributeSettings()
        if self.rotate is None:
            self.rotate = AttributeSettings()
        if self.scale is None:
            self.scale = AttributeSettings()


# Common attribute configurations
ATTR_CONFIG_ROTATION_ONLY = TransformAttributeConfig(
    translate=AttributeSettings(keyable=False, visible=False, locked=True),
    rotate=AttributeSettings(keyable=True, visible=True, locked=False),
    scale=AttributeSettings(keyable=False, visible=False, locked=True),
)

ATTR_CONFIG_ALL_UNLOCKED = TransformAttributeConfig(
    translate=AttributeSettings(keyable=True, visible=False, locked=False),
    rotate=AttributeSettings(keyable=True, visible=False, locked=False),
    scale=AttributeSettings(keyable=True, visible=True, locked=True),
)

ATTR_CONFIG_FK_LIMB = TransformAttributeConfig(
    translate=AttributeSettings(keyable=False, visible=False, locked=True),
    rotate=AttributeSettings(keyable=True, visible=True, locked=False),
    scale=AttributeSettings(keyable=False, visible=False, locked=True),
)

ATTR_CONFIG_IK_LIMB = TransformAttributeConfig(
    translate=AttributeSettings(keyable=True, visible=True, locked=False),
    rotate=AttributeSettings(keyable=True, visible=True, locked=False),
    scale=AttributeSettings(keyable=False, visible=False, locked=True),
)

ATTR_CONFIG_SWITCH = TransformAttributeConfig(
    translate=AttributeSettings(keyable=False, visible=False, locked=True),
    rotate=AttributeSettings(keyable=False, visible=False, locked=True),
    scale=AttributeSettings(keyable=False, visible=False, locked=True),
)

AXIS_LIST = ["X", "Y", "Z"]


# ============================================================================
# Attribute State Management using Wrapper
# ============================================================================


def set_attribute_value_om2(
    node_name: str, attr_name: str, value: Any
) -> bool:
    """Set attribute value using wrapper.

    Args:
        node_name: Node name.
        attr_name: Attribute name.
        value: Value to set.

    Returns:
        True if successful.
    """
    node = get_node(node_name)
    if node:
        try:
            return node.setAttribute(attr_name, value)
        except (RuntimeError, KeyError):
            pass
    return False


def get_attribute_value(node_name: str, attr_name: str) -> Any:
    """Get attribute value using wrapper.

    Args:
        node_name: Node name.
        attr_name: Attribute name.

    Returns:
        Attribute value or None.
    """
    plug = get_plug(node_name, attr_name)
    if plug:
        return plug.value()
    return None


def set_plug_value(plug: wrapper.Plug, value: Any) -> bool:
    """Set a plug value using wrapper.

    Args:
        plug: The Plug wrapper to set.
        value: The value to set.

    Returns:
        True if successful.
    """
    if plug:
        try:
            plug.set(value)
            return True
        except RuntimeError:
            pass
    return False


# ============================================================================
# Attribute Cleanup Functions
# ============================================================================


def cleanup_attributes(
    node_name: str, config: TransformAttributeConfig
) -> None:
    """Clean up transform attributes on a node based on configuration.

    Uses wrapper for attribute manipulation.

    Args:
        node_name: Name of the node to clean up.
        config: Attribute configuration to apply.
    """
    if not node_exists(node_name):
        logger.warning(f"Node does not exist: {node_name}")
        return

    node = get_node(node_name)
    if not node:
        return

    for axis in AXIS_LIST:
        # Translate
        _set_attribute_state(
            node,
            f"translate{axis}",
            config.translate.keyable,
            config.translate.visible,
            config.translate.locked,
        )

        # Rotate
        _set_attribute_state(
            node,
            f"rotate{axis}",
            config.rotate.keyable,
            config.rotate.visible,
            config.rotate.locked,
        )

        # Scale
        _set_attribute_state(
            node,
            f"scale{axis}",
            config.scale.keyable,
            config.scale.visible,
            config.scale.locked,
        )

    _ensure_keyable_state(node_name)
    cmds.delete(node_name, constructionHistory=True)


def _set_attribute_state(
    node: wrapper.DGNode,
    attr_name: str,
    keyable: bool,
    visible: bool,
    locked: bool,
) -> None:
    """Set the state of a single attribute using wrapper.

    Args:
        node: Wrapper node.
        attr_name: Attribute name.
        keyable: If True, make attribute keyable.
        visible: If True, show in channel box.
        locked: If True, lock the attribute.
    """
    try:
        plug = node.attribute(attr_name)
        if not plug:
            return

        # First unlock to allow changes
        if plug.isLocked:
            plug.lock(False)

        # Set keyable and channel box states using the plug's MPlug
        mplug = plug.plug()
        mplug.isKeyable = keyable
        if not keyable:
            mplug.isChannelBox = visible

        # Set locked state
        if locked:
            plug.lock(True)

    except (RuntimeError, KeyError) as e:
        logger.debug(
            f"Could not set attribute state for {node.name()}.{attr_name}: {e}"
        )


def _ensure_keyable_state(node_name: str) -> None:
    """Ensure keyable attributes are properly set.

    Args:
        node_name: Node name.
    """
    node = get_node(node_name)
    if not node:
        return

    for axis in AXIS_LIST:
        for attr_type in ["translate", "rotate", "scale"]:
            attr_name = f"{attr_type}{axis}"
            try:
                plug = node.attribute(attr_name)
                if plug:
                    mplug = plug.plug()
                    if mplug.isChannelBox and not mplug.isKeyable:
                        mplug.isKeyable = True
            except (RuntimeError, KeyError):
                pass


# ============================================================================
# Attribute Locking/Unlocking
# ============================================================================


def lock_attributes(node_name: str, attributes: List[str]) -> None:
    """Lock specified attributes on a node using wrapper.

    Args:
        node_name: Node name.
        attributes: List of attribute names to lock.
    """
    node = get_node(node_name)
    if not node:
        return

    for attr in attributes:
        try:
            plug = node.attribute(attr)
            if plug:
                plug.lock(True)
                plug.plug().isKeyable = False
        except (RuntimeError, KeyError):
            pass


def unlock_attributes(node_name: str, attributes: List[str]) -> None:
    """Unlock specified attributes on a node using wrapper.

    Args:
        node_name: Node name.
        attributes: List of attribute names to unlock.
    """
    node = get_node(node_name)
    if not node:
        return

    for attr in attributes:
        try:
            plug = node.attribute(attr)
            if plug:
                plug.lock(False)
                plug.plug().isKeyable = True
        except (RuntimeError, KeyError):
            pass


def hide_attributes(node_name: str, attributes: List[str]) -> None:
    """Hide specified attributes from the channel box using wrapper.

    Args:
        node_name: Node name.
        attributes: List of attribute names to hide.
    """
    node = get_node(node_name)
    if not node:
        return

    for attr in attributes:
        try:
            plug = node.attribute(attr)
            if plug:
                mplug = plug.plug()
                mplug.isKeyable = False
                mplug.isChannelBox = False
        except (RuntimeError, KeyError):
            pass


# ============================================================================
# Attribute Creation using Wrapper
# ============================================================================


def add_float_attribute(
    node_name: str,
    long_name: str,
    short_name: Optional[str] = None,
    default_value: float = 0.0,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    keyable: bool = True,
    locked: bool = False,
) -> str:
    """Add a float attribute to a node using wrapper.

    Args:
        node_name: Node name.
        long_name: Long name for the attribute.
        short_name: Short name for the attribute.
        default_value: Default value.
        min_value: Minimum value.
        max_value: Maximum value.
        keyable: If True, make attribute keyable.
        locked: If True, lock the attribute.

    Returns:
        Full attribute path.
    """
    node = get_node(node_name)
    if not node:
        return f"{node_name}.{long_name}"

    # Check if attribute already exists
    if node.hasAttribute(long_name):
        return f"{node_name}.{long_name}"

    # Use wrapper's addAttribute
    kwargs = {
        "type": attributetypes.kMFnNumericFloat,
        "keyable": keyable,
        "default": default_value,
    }

    if min_value is not None:
        kwargs["min"] = min_value

    if max_value is not None:
        kwargs["max"] = max_value

    try:
        plug = node.addAttribute(long_name, **kwargs)
        if locked and plug:
            plug.lock(True)
    except RuntimeError:
        # Fallback to cmds
        attr_kwargs = {
            "longName": long_name,
            "attributeType": "float",
            "keyable": keyable,
            "defaultValue": default_value,
        }
        if short_name:
            attr_kwargs["shortName"] = short_name
        if min_value is not None:
            attr_kwargs["minValue"] = min_value
        if max_value is not None:
            attr_kwargs["maxValue"] = max_value

        cmds.addAttr(node_name, **attr_kwargs)
        if locked:
            cmds.setAttr(f"{node_name}.{long_name}", lock=True)

    return f"{node_name}.{long_name}"


def add_enum_attribute(
    node_name: str,
    long_name: str,
    short_name: Optional[str] = None,
    enum_names: List[str] = None,
    default_value: int = 0,
    keyable: bool = True,
) -> str:
    """Add an enum attribute to a node using wrapper.

    Args:
        node_name: Node name.
        long_name: Long name for the attribute.
        short_name: Short name for the attribute.
        enum_names: List of enum option names.
        default_value: Default enum index.
        keyable: If True, make attribute keyable.

    Returns:
        Full attribute path.
    """
    node = get_node(node_name)
    if not node:
        return f"{node_name}.{long_name}"

    # Check if attribute already exists
    if node.hasAttribute(long_name):
        return f"{node_name}.{long_name}"

    enum_names = enum_names or ["option1", "option2"]

    # Use wrapper's addAttribute
    try:
        plug = node.addAttribute(
            long_name,
            type=attributetypes.kMFnkEnumAttribute,
            keyable=keyable,
            enums=enum_names,
            default=default_value,
        )
    except (RuntimeError, TypeError):
        # Fallback to cmds
        enum_str = ":".join(enum_names) + ":"
        cmds.addAttr(
            node_name,
            longName=long_name,
            shortName=short_name or long_name,
            attributeType="enum",
            enumName=enum_str,
            keyable=keyable,
        )
        cmds.setAttr(f"{node_name}.{long_name}", default_value)

    return f"{node_name}.{long_name}"


def add_string_attribute(
    node_name: str, attr_name: str, value: str = ""
) -> str:
    """Add a string attribute to a node using wrapper.

    Args:
        node_name: Node name.
        attr_name: Attribute name.
        value: String value to set.

    Returns:
        Full attribute path.
    """
    node = get_node(node_name)
    if not node:
        return f"{node_name}.{attr_name}"

    # Check if attribute already exists
    if not node.hasAttribute(attr_name):
        try:
            node.addAttribute(attr_name, type=attributetypes.kMFnDataString)
        except (RuntimeError, TypeError):
            # Fallback to cmds
            cmds.addAttr(node_name, longName=attr_name, dataType="string")

    # Set value
    try:
        node.setAttribute(attr_name, value)
    except (RuntimeError, KeyError):
        cmds.setAttr(f"{node_name}.{attr_name}", value, type="string")

    return f"{node_name}.{attr_name}"


# ============================================================================
# Attribute Connections using Wrapper
# ============================================================================


def connect_attribute(source: str, target: str, force: bool = True) -> bool:
    """Connect two attributes using wrapper.

    Args:
        source: Source attribute (node.attr).
        target: Target attribute (node.attr).
        force: If True, force the connection.

    Returns:
        True if connection was successful.
    """
    try:
        source_plug = wrapper.plug_by_name(source)
        target_plug = wrapper.plug_by_name(target)

        if source_plug and target_plug:
            source_plug.connect(target_plug)
            return True
    except (RuntimeError, wrapper.InvalidPlugPathError):
        pass

    # Fallback to cmds
    try:
        cmds.connectAttr(source, target, force=force)
        return True
    except RuntimeError as e:
        logger.debug(f"Could not connect {source} to {target}: {e}")
        return False


def disconnect_attribute(source: str, target: str) -> bool:
    """Disconnect two attributes using wrapper.

    Args:
        source: Source attribute.
        target: Target attribute.

    Returns:
        True if disconnection was successful.
    """
    try:
        source_plug = wrapper.plug_by_name(source)
        target_plug = wrapper.plug_by_name(target)

        if source_plug and target_plug:
            source_plug.disconnect(target_plug)
            return True
    except (RuntimeError, wrapper.InvalidPlugPathError):
        pass

    # Fallback to cmds
    try:
        cmds.disconnectAttr(source, target)
        return True
    except RuntimeError:
        return False


def delete_if_exists(name: str) -> bool:
    """Delete an object if it exists using wrapper.

    Args:
        name: Name of the object to delete.

    Returns:
        True if object was deleted.
    """
    node = get_node(name)
    if node and node.exists():
        try:
            return node.delete()
        except RuntimeError:
            # Fall back to cmds
            try:
                cmds.delete(name)
                return True
            except RuntimeError:
                return False
    return False
