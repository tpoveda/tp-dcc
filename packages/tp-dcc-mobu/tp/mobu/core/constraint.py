#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with constraints for MotionBuilder
"""


import pyfbsdk

from tp.core import log

logger = log.tpLogger

CONSTRAINT_TYPES = dict((pyfbsdk.FBConstraintManager().TypeGetName(i), i) for i in range(
    pyfbsdk.FBConstraintManager().TypeGetCount()))


def get_constraint_by_name(name, include_namespace=True):
    """
    Returns a constraint that matches given long name
    :param name: str, name of the constraint
    :param include_namespace: bool, Whether or not to include node namespace
    :return:
    """

    for constraint in pyfbsdk.FBSystem().Scene.Constraints:
        constraint_name = constraint.LongName if include_namespace else constraint.Name
        if name != constraint_name:
            continue

        return constraint


def get_constraint_by_type(constraint_type):
    """
    Returns a list of constraints in the current scene of the given type
    :param constraint_type: str, constraint type ('Aim', 'Position', etc)
    :return:
    """

    found_constraints = list()

    for constraint in pyfbsdk.FBSystem().Scene.Constraints:
        class_type = getattr(pyfbsdk.kConstraintClassDict.get(constraint.Description), 'constraintType')
        if constraint_type != class_type:
            continue
        found_constraints.append(constraint)

    return found_constraints


def create_constraint(constraint_type, name=None):
    """
    Creates a constraint with the given type
    :param constraint_type: str, constraint type found in CONSTRAINT_TYPES
    :param name: str, optional name to give to constraint.
    :return:
    """

    try:
        constraint = pyfbsdk.FBConstraintManager().TypeCreateConstraint(pyfbsdk.kConstraintTypes[constraint_type])
    except KeyError:
        raise Exception('Invalid constraint type given: "{}"'.format(constraint_type))

    pyfbsdk.FBSystem().Scene.Constraints.append(constraint)

    if name:
        constraint.Name = name

    return constraint

