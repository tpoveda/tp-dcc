from __future__ import annotations

from maya.api import OpenMaya, OpenMayaAnim

from . import timerange


def serialize_animation_curve(anim_curve_node: OpenMaya.MObject) -> dict:
    """Serialize the given animation curve node.

    Args:
        anim_curve_node: Maya object representing the animation curve to
            serialize.

    Returns:
        JSON valid dictionary with the animation curve data.
    """

    anim_curve = OpenMayaAnim.MFnAnimCurve(anim_curve_node)
    num_keys = anim_curve.numKeys
    frames = [0] * num_keys
    values = [0] * num_keys
    in_tangents = [0] * num_keys
    out_tangents = [0] * num_keys
    in_tangent_angles = [0] * num_keys
    out_tangent_angles = [0] * num_keys
    in_tangent_weights = [0] * num_keys
    out_tangent_weights = [0] * num_keys
    for num in range(num_keys):
        input_value = anim_curve.input(num)
        frame = input_value.value
        value = anim_curve.value(num)
        in_tangent_type = anim_curve.inTangentType(num)
        out_tangent_type = anim_curve.outTangentType(num)
        in_tangent_angle, in_tangent_weight = anim_curve.getTangentAngleWeight(
            num, True
        )
        out_tangent_angle, out_tangent_weight = anim_curve.getTangentAngleWeight(
            num, False
        )
        frames[num] = frame
        values[num] = value
        in_tangents[num] = in_tangent_type
        out_tangents[num] = out_tangent_type
        in_tangent_angles[num] = in_tangent_angle.value
        out_tangent_angles[num] = out_tangent_angle.value
        in_tangent_weights[num] = in_tangent_weight
        out_tangent_weights[num] = out_tangent_weight

    return {
        "space": OpenMaya.MSpace.kObject,
        "preInfinity": anim_curve.preInfinityType,
        "postInfinity": anim_curve.postInfinityType,
        "weightTangents": anim_curve.isWeighted,
        "frameRate": timerange.current_time_info()["fps"],
        "frames": frames,
        "values": values,
        "inTangents": in_tangents,
        "outTangents": out_tangents,
        "inTangentAngles": in_tangent_angles,
        "outTangentAngles": out_tangent_angles,
        "inTangentWeights": in_tangent_weights,
        "outTangentWeights": out_tangent_weights,
        "curveType": anim_curve.animCurveType,
    }
