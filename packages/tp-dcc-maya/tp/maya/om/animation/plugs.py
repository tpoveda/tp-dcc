from __future__ import annotations

import maya.api.OpenMaya as OpenMaya

from tp.maya.om import plugs
from tp.maya.om.animation import animlayers


def is_animation_blend(obj: OpenMaya.MObject) -> bool:
    """
    Returns whether given object is an animation blend.

    :param OpenMaya.MObject obj: object to check.
    :return: True if given node is an animation blend; False otherwise.
    :rtype: bool
    """

    # FIXME: `MObject::hasFn` does not accept `MFn::kBlendNodeBase`
    return obj.apiTypeStr.startswith('kBlendNode')


def find_animated_plug(plug: OpenMaya.MPlug) -> OpenMaya.MPlug:
    """
    Returns the plug that is currently being animated on.
    If the plug is being used by an animation layer, then the input plug from the blend node will be returned.

    :param OpenMaya.MPlug plug: plug to find animated plug from.
    :return: animated plug.
    :rtype: OpenMaya.MPlug
    :raises TypeError: if animation layer is not valid.
    """

    is_animated = plugs.is_animated(plug)
    if not is_animated:
        return plug

    # Evaluate incoming connection
    source_node = plug.source().node()

    if not is_animation_blend(source_node):
        return plug

    # Get active/preferred animation layer
    best_layer = animlayers.best_animation_layer(plug)
    if best_layer.isNull():
        raise TypeError(f'findAnimLayerCurve() "{plug.info}" is not in an anim-layer!')

    # Get animation blend associated with animation layer
    anim_blends = getMemberBlends(plug)
    input_plug: OpenMaya.MPlug | None = None

    if isBaseAnimLayer(best_layer):
        input_plug = plugs.find_plug(anim_blends[0], 'inputA')
    else:
        attribute = attributeutils.findAttribute(best_layer, 'blendNodes')
        anim_layers = [plugutils.findConnectedMessage(blend, attribute=attribute).node() for blend in anim_blends]
        index = anim_layers.index(best_layer)
        input_plug = plugutils.findPlug(anim_blends[index], 'inputB')

    # Check if this is a compound plug. If so, then get the associated indexed child plug.
    if not input_plug.isCompound:
        return input_plug

    input_children = list(plugutils.iterChildren(input_plug))
    plug_children = list(plugutils.iterChildren(plug.parent()))
    index = plug_children.index(plug)
    return input_children[index]
