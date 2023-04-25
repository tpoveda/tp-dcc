#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Unreal Control Rig
"""

import unreal

from tp.unreal.core import asset


class BoneTypes(object):
    IMPORTED = unreal.RigBoneType.IMPORTED
    USER = unreal.RigBoneType.USER


def create_control_rig_blueprint(asset_path, unique_name=True):
    """
    Creates a new control rig blueprint
    :param asset_path: str
    :param unique_name: bool
    :return: unreal.ControlRigBlueprint
    """

    control_rig_bp = asset.create_asset(
        asset_path, unique_name=unique_name,
        asset_class=unreal.ControlRigBlueprint, asset_factory=unreal.ControlRigBlueprintFactory())

    return control_rig_bp


def get_hierarchy_modifier(control_rig_asset_path):
    """
    Returns hierarchy modifier instance of the given control rig blueprint asset
    :param control_rig_asset_path: str
    :return: unreal.ControlRigHierarchyModifier or None
    """

    control_rig = asset.get_asset(control_rig_asset_path)
    if not control_rig:
        return None

    return control_rig.get_hierarchy_modifier()


def add_bone(control_rig_asset_path, bone_name='new_bone', parent_name=None, bone_type=None):
    """
    Adds a new bone in the hierarchy of the given control rig asset
    :param control_rig_asset_path: str
    :param bone_name: str
    :param parent_name: str
    :param bone_type: unreal.RigBoneType or BoneTypes
    :return:
    """

    hierarchy_mod = get_hierarchy_modifier(control_rig_asset_path)
    if not hierarchy_mod:
        return None

    parent_name = str(parent_name)
    bone_type = bone_type or BoneTypes.USER

    return hierarchy_mod.add_bone(bone_name, parent_name=parent_name, type=bone_type)


def get_selected_hierarchy_elements(control_rig_asset_path):
    """
    Returns selected elements on given control rig blueprint rig hierarchy
    :param control_rig_asset_path: str
    :return: list(unreal.RigElementKey)
    """

    hierarchy_mod = get_hierarchy_modifier(control_rig_asset_path)
    if not hierarchy_mod:
        return list()

    return hierarchy_mod.get_selection() or list()


def export_elements_to_text(control_rig_asset_path, rig_elements):
    """
    Exports the elements provided to text
    :param rig_elements: list(unreal.RigElementKey)
    :return: str
    """

    if not rig_elements:
        return ''

    hierarchy_mod = get_hierarchy_modifier(control_rig_asset_path)
    if not hierarchy_mod:
        return ''

    return hierarchy_mod.export_to_text(rig_elements)


def export_selected_elements_to_text(control_rig_asset_path):
    """
    Exports selected elements to text
    :param control_rig_asset_path: str
    :return: str
    """

    selected_elements = get_selected_hierarchy_elements(control_rig_asset_path)

    return export_elements_to_text(control_rig_asset_path, selected_elements)
