#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains exceptions related with Maya API
"""


class MayaError(Exception):
    """
    Base custom class for all Maya API exceptions.
    """

    pass


class ObjectDoesNotExistError(MayaError):
    """
    Raised anytime the current object is operated on and does not exist.
    """

    pass


class MissingObjectByNameError(MayaError):
    """
    Custom exception raised when we try to find an object by name but it does not exists within current Maya scene.
    """

    pass


class ReferenceObjectError(MayaError):
    """
    Raised when an object is a reference and the requested operation is not allowed on a reference.
    """

    pass


class AttributeAlreadyExistsError(MayaError):
    """
    Custom exception raised when trying to add an attribute that already exists.
    """

    pass


class InvalidPlugPathError(MayaError):
    """
    Custom exception raised when a plug path is not valid.
    """

    pass
