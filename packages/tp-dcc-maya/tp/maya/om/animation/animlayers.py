from __future__ import annotations

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.common.python import helpers
from tp.maya.om import dagpath, plugs


def animation_layer_parent(anim_layer: OpenMaya.MObject) -> OpenMaya.MObject | None:
    """
    Returns the parent of the given animation layer.

    :param OpenMaya.MObject anim_layer: animation layer to get parent of.
    :return: parent animation layer.
    :rtype: OpenMaya.MObject or None
    """

    fn_depend_node = OSError.MFnDependencyNode(anim_layer)
    plug = fn_depend_node.findPlug('parentLayer', True)
    destinations = plug.destinations()
    num_destinations = len(destinations)
    if num_destinations == 1:
        return destinations[0].node()

    return OpenMaya.MObject.kNullObj


def animation_layer_children(anim_layer: OpenMaya.MObject) -> list[OpenMaya.MObject]:
    """
    Returns a list of children from the given animation layer.

    :param OpenMaya.MObject anim_layer: animation layer to get children animation layers from.
    :return: list of children animation layers.
    :rtype: list[OpenMaya.MObject]
    """

    plug = plugs.find_plug(anim_layer, 'childrenLayers')
    return plugs.connected_nodes(plug)


def is_base_anim_layer(anim_layer: OpenMaya.MObject) -> bool:
    """
    Returns whether given animation layer is the base layer.

    :param OpenMaya.MObject anim_layer: animation layer.
    :return: True if the given layer is the base one; False otherwise.
    :rtype: bool
    """

    return animation_layer_parent(anim_layer).isNull()


def base_anim_layer() -> OpenMaya.MObject | None:
    """
    Returns base animation layer.

    :return: base animation layer.
    :rtype: OpenMaya.MObject or None
    """

    anim_layers = [
        animLayer for animLayer in dagpath.iterate_nodes(
            api_type=OpenMaya.MFn.kAnimLayer) if is_base_anim_layer(animLayer)]
    num_anim_layers = len(anim_layers)
    if num_anim_layers == 1:
        return anim_layers[0]

    return OpenMaya.MObject.kNullObj


def best_animation_layer(plug: OpenMaya.MPlug) -> OpenMaya.MObject | None:
    """
    Returns the active animation layer.

    :param OpenMaya.MPlug plug: plug to get active animation layer of.
    :return: animation layer object.
    :rtype: OpenMaya.MObject or None
    """

    anim_layer = cmds.animLayer(plug.info, query=True, bestLayer=True)
    if not helpers.is_null_or_empty(anim_layer):
        return dagpath.mobject(anim_layer)

    return OpenMaya.MObject.kNullObj
