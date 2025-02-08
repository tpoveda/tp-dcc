from __future__ import annotations

from maya import cmds


def xray_curves(curve_shapes: list[str], xray: bool):
    """
    Sets the given curve shapes to be xray.

    :param curve_shapes: List of curve shapes to set as xray.
    :param xray: Whether to set the curve shapes as xray or not.
    """

    for curve_shape in curve_shapes:
        if cmds.attributeQuery("alwaysDrawOnTop", node=curve_shape, exists=True):
            cmds.setAttr(curve_shape + ".alwaysDrawOnTop", xray)


def xray_curve_selected(xray: bool):
    """
    Sets the selected curve shapes to be xray.

    :param xray: Whether to set the curve shapes as xray or not.
    """

    xray_curves(
        cmds.listRelatives(cmds.ls(selection=True) or [], shapes=True) or [], xray
    )
