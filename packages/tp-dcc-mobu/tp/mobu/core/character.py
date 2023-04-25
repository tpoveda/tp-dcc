#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with MotionBuilder characters
"""

import os
try:
    import pickle
except ImportError:
    import cPickle as pickle

import pyfbsdk

from tp.core import log
from tp.common.python import python
from tp.mobu.core import node, property

logger = log.tpLogger


def create_character(name):
    """
    Creates a new character
    :param name: str
    :return: FBCharacter
    """

    return pyfbsdk.FBCharacter(name)


def get_character_node_by_name(name):
    """
    Returns character node with given long name from current scene
    :param name: str
    :return: FBCharacter or None
    """

    for character_node in pyfbsdk.FBSystem().Scene.Characters:
        if name != character_node.LongName:
            continue

        return character_node


def get_character_slots(character_node, return_names=False):
    """
    Returns list of character mapping slots
    :param character_node: FBCharacter
    :param return_names: bool, Whether to return the slot name or the property object
    :return: str or
    """

    slots = property.list_properties(character_node, pattern='*Link', property_type='Object')

    if return_names:
        return map(lambda x: x.GetName(), slots)

    return slots


def get_slot_model(character_node, slot):
    """
    Returns the model from the given slot
    :param character_node: FBCharacter
    :param slot:
    :return:
    """

    try:
        return character_node.PropertyList.Find(slot)[0]
    except IndexError:
        return None


def set_slot_model(character_node, slot, model):
    """
    Adds a model to a slot in the characterization map
    :param character_node: FBCharacter
    :param slot: str, full name of character slot
    :param model: str or FBModel, model to add to the slot (can be name or model object)
    :return:
    """

    if python.is_string(model):
        obj = node.get_model_node_by_name(model)
        if not obj:
            logger.warning(
                'Object "{}" does not exist. Unable to add it to the character map "{}" under slot "{}"'.format(
                    model, character_node.Name, slot))
            return False
    else:
        obj = model

    character_slot = property.list_properties(pattern=slot)
    if not character_slot:
        logger.warning('Invalid character slot "{}"'.format(slot))
        return False

    # remove all current models from the slot
    character_slot[0].removeAll()

    if obj:
        character_slot[0].append(obj)

    return True


def remove_slot_model(character_node, slot):
    """
    Removes the current model from the given slot in the given character node
    :param character_node: FBCharacter
    :param slot: str, full name of character slot
    :return:
    """

    return set_slot_model(character_node, slot, None)


def get_character_mapping(character_node, return_names=True, skip_empty=True, strip_prefix=None):
    """
    Returns a dictionary of slot/model in the character mapping
    :param character_node: FBCharacter
    :param return_names: bool, Whether to return names as strings or FBModel objects
    :param skip_empty: bool, Whether or not to skip over slots that are empty
    :param strip_prefix: str, removes this prefix form name of the model
    :return: dict
    """

    mapping = dict()

    character_slots = get_character_slots(character_node)
    if not character_slots:
        return mapping

    for slot in character_slots:
        if not slot:
            if skip_empty:
                continue
            else:
                model = None
        else:
            model = slot[0]

        if return_names:
            slot = slot.GetName()
            if model:
                model = model.LongName
                if strip_prefix:
                    model = model.replace(strip_prefix, '')

        mapping[slot] = model

    return mapping


def export_mapping(character_node, file_path, strip_prefix=None):
    """
    Saves the character map as a template for later use
    :param character_node: FBCharacter
    :param file_path: str, file to store the mapping in
    :param strip_prefix: str, remove given prefix from the model name
    :return: bool
    """

    mapping = get_character_mapping(character_node, return_names=True, skip_empty=False, strip_prefix=strip_prefix)
    if not mapping:
        return False

    with open(file_path, 'w') as file_handle:
        pickle.dump(mapping, file_handle, 0)

    return True


def import_mapping(character_node, file_path, add_prefix=None, raise_exception=True):
    """
    Applies a character template to the given character node
    :param character_node: FBCharacter
    :param file_path: str, character mapping to import
    :param add_prefix: str, append given prefix onto the model names
    :param raise_exception: bool, Whether or not raise an exception if a slot or model is not found
    :return: bool
    """

    if not file_path or not os.path.isfile(file_path):
        return False

    with open(file_path, 'r') as file_handle:
        dump_data = pickle.load(file_handle)
    if not dump_data:
        return False

    for slot, model in dump_data.items():
        if model and add_prefix:
            model = '{}{}'.format(add_prefix, model)
        try:
            set_slot_model(character_node, slot, model)
        except Exception:
            if raise_exception:
                raise
