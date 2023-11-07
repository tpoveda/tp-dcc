from __future__ import annotations

from typing import Any

import maya.api.OpenMaya as OpenMaya

from tp.maya.om import plugs


def as_bool(plug: OpenMaya.MPlug, **kwargs: dict) -> bool:
    """
    Returns the boolean value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve boolean value from.
    :param dict kwargs: keyword arguments.
    :return: boolean value.
    :rtype: bool
    """

    return plug.asBool()


def as_int(plug, **kwargs) -> int:
    """
    Returns the integer value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve integer value from.
    :param dict kwargs: keyword arguments.
    :return: integer value.
    :rtype: int
    """

    return plug.asInt()


def as_float(plug, **kwargs) -> float:
    """
    Returns the float value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve float value from.
    :param dict kwargs: keyword arguments.
    :return: float value.
    :rtype: float
    """

    return plug.asFloat()


def value(plug: OpenMaya.MPlug, convert_units: bool = True, best_layer: bool = False) -> Any:
    """
    Returns the value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve value of.
    :param bool convert_units: whether to convert internal values to UI values.
    :param bool best_layer: whether the value from the active animation layer is returned instead.
    :return: plug value.
    :rtype: Any
    """

    if plug.isNull:
        return None

    # Evaluate plug type
    if plug.isArray and not plug.isElement:
        indices = plug.getExistingArrayAttributeIndices()
        num_indices = len(indices)
        plug_values = [None] * num_indices
        for (physical_index, logical_index) in enumerate(indices):
            element = plug.elementByLogicalIndex(logical_index)
            plug_values[physical_index] = value(element, convert_units=convert_units)
        return plug_values
    elif plugs.is_compound_numeric(plug):
        # Return list of values from parent plug
        return [value(child, convert_units=convert_units) for child in plugs.iterate_children(plug, recursive=False)]
    else:
        # Check if active anim-layer should be evaluated
        if best_layer and plugs.is_animated(plug):
            plug = animutils.findAnimatedPlug(plug)
            return value(plug, convert_units=convert_units)

        # Get value from plug
        # Check if any units require converting
        #
        attribute_type = plugutils.getApiType(plug)
        plug_value = __get_value__[attribute_type](plug)

        if convert_units and isinstance(plug_value, (OpenMaya.MDistance, OpenMaya.MAngle, OpenMaya.MTime)):
            return plug_value.asUnits(plug_value.iUnit())

        return plug_value
