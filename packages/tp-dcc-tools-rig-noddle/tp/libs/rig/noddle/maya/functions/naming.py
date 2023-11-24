from __future__ import annotations

import re
from typing import List

import pymel.core as pm

from tp.core import log
from tp.common.python import helpers
from tp.preferences.interfaces import noddle

logger = log.rigLogger


def naming_template() -> str:
    """
    Returns the current naming template to use.

    :return: naming template to use. Eg. '{side}_{name}_{suffix}'
    :rtype: str
    """

    noddle_preferences = noddle.noddle_interface()
    all_templates = noddle_preferences.naming_templates()
    current_name = noddle_preferences.current_naming_template()
    return all_templates.get(current_name)


def generate_name(name: str | List[str], side: str, suffix: str, override_index: int | None = None) -> str:
    """
    Generates a new node name.

    :param str or List[str] name: base name.
    :param str side: side name.
    :param str suffix: suffix to add to the final node name.
    :param int or None override_index: optional index length to override.
    :return: generated name.
    :rtype: str
    """

    noddle_preferences = noddle.noddle_interface()
    name = '_'.join(name) if isinstance(name, (list, tuple)) else name
    timeout = 300
    template = naming_template()
    index = noddle_preferences.name_start_index()
    zfill = noddle_preferences.name_index_padding()
    index_str = str(index).zfill(zfill) if override_index is None else override_index
    indexed_name = f'{name}_{index_str}'
    full_name = template.format(side=side, name=indexed_name, suffix=suffix)
    while pm.objExists(full_name):
        index += 1
        index_str = str(index).zfill(zfill) if override_index is None else override_index
        indexed_name = f'{name}_{index_str}'
        full_name = template.format(side=side, name=indexed_name, suffix=suffix)
        if index == timeout:
            logger.warning(f'Reached maximum number of iterations ({timeout}')
            break

    return full_name


def deconstruct_name(node_name: str) -> helpers.ObjectDict:
    """
    Deconstruct given node name to tokens using template.

    :param str node_name: name we want to deconstruct
    :return: deconstructed name dictionary.
    :rtype: helpers.ObjectDict
    """

    template = naming_template()
    name_parts = node_name.split('_')

    re_index = re.compile(r"\d+|^$")
    all_indexes = list(filter(re_index.match, name_parts))
    index_index = len(name_parts) - name_parts[::-1].index(all_indexes[-1]) - 1
    index = name_parts[index_index]

    name_start_index = template.split('_').index('{name}')
    name = '_'.join(name_parts[name_start_index:index_index])
    indexed_name = '_'.join(name_parts[name_start_index:index_index + 1])

    temp_name = node_name.replace(indexed_name, 'name')
    side_index = template.split('_').index('{side}')
    suffix_index = template.split('_').index('{suffix}')
    side = temp_name.split('_')[side_index]
    suffix = temp_name.split('_')[suffix_index]

    data = helpers.ObjectDict()
    data.update({
        'side': side,
        'name': name,
        'indexed_name': indexed_name,
        'index': index,
        'suffix': suffix
    })

    return data
