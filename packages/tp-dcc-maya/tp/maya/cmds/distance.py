#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with attributes
"""


def get_closest_distance_info(source=None, targets=None, mode='close', res_mode='point', source_pivot='rp',
                              target_pivot='rp'):
    """
    Returns the closest return based on a source and target and given modes
    :param source: str, base object to measure from
    :param targets: list<stt>, list of object types
    :param mode: str, what mode we are checking dat from (close or far)
    :param res_mode: str
        - object: return the [closest] target
        - point: retur the [closest] point
        - component: resturn the [closest] base component
        - pointOnSurface: [closest] point on the target shape(s)
        - pointOnSurfaceLoc: [closest] point on target shape(s) loc'd
        - shape: gets closest point on every shape, returns closest
    :param source_pivot: str
    :param target_pivot:str
    :return: tuple(res, distance)
    """

    fn_name = 'get_closest_distance_info'

    def get_from_targets(source_pos, targets, target_pivot, res_mode, mode):
        pass

    dist_modes_dict = {'close': ['closest', 'c', 'near'], 'far': ['furthest', 'long']}
    source = None
