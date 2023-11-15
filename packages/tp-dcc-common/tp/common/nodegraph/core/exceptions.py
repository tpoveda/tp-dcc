#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom exceptions used by tp-libs-nodegraph
"""


class NodePropertyError(Exception):
	pass


class NodeRegistrationError(Exception):
	pass


class SocketDuplicatedError(Exception):
	pass


class InvalidDataTypeRegistrationError(Exception):
	pass


class SocketError(Exception):
	pass


class NodeMenuError(Exception):
	pass


class NodeWidgetError(Exception):
	pass


class SocketRegistrationError(Exception):
	pass
