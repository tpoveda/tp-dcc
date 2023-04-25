#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions to work with Photoshop documents
"""


def find_layers(layer):
    """
    Get all layers from a PSD layer
    """

    layers = list()
    is_group = False
    try:
        layer.layers
        is_group = True
    except Exception:
        pass

    if is_group:
        for grp_layer in layer.layers:
            find_layers(grp_layer)
    else:
        layers.append(layer)
    return layers
