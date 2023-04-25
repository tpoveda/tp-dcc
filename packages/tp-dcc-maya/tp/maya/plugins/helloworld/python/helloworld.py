#! /usr/bin/env python

"""
Python Hello World Command plugin for Maya
"""


from __future__  import print_function, division, absolute_import, unicode_literals


__author__ = "Tomas Poveda"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import maya.OpenMayaMPx as OpenMayaMPx


class HelloWorldPyCmd(OpenMayaMPx.MPxCommand, object):

    command = "HelloWorldPy"

    def __init__(self):
        super(HelloWorldPyCmd, self).__init__()

    def doIt(self, args):
        print('Hello World')

def creator():
    return OpenMayaMPx.asMPxPtr(HelloWorldPyCmd())

def initializePlugin(mobj):
    mplugin = OpenMayaMPx.MFnPlugin(mobj)
    try:
        mplugin.registerCommand(HelloWorldPyCmd.command, creator)
    except:
        raise Exception('Failed to register command: {}'.format(HelloWorldPyCmd.command))

def uninitializePlugin(mobj):
    mplugin = OpenMayaMPx.MFnPlugin(mobj)
    try:
        mplugin.deregisterCommand(HelloWorldPyCmd.command)
    except:
        raise Exception('Failed to unregister command: {}'.format(HelloWorldPyCmd.command))

HelloWorldPyCmd().doIt("")
