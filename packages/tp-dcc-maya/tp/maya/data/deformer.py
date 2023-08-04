#! /usr/bin/env python

"""
This module include base class for deformer data object
"""

import copy
import logging

import maya.cmds as cmds

from tpDcc.libs.python import python

LOGGER = logging.getLogger('tpDcc-dccs-maya')


class MayaDeformerData(object):
    """
    Base class for deformer data objects
    This class contains functions to save and load deformers data
    """

    def __init__(self, deformer=''):
        super(MayaDeformerData, self).__init__()

        # Common deformer data
        self._data['name'] = ''
        self._data['type'] = ''
        self._data['affectedGeometry'] = list()

        # Deformer definition attributes
        self._data['attrValueList'] = ['envelope']
        self._data['attrConnectionList'] = []

        # Deformer storage attributes
        self._data['attrValueDict'] = {}
        self._data['attrConnectionDict'] = {}

        self._deformer = deformer
        if deformer:
            self.build_data()

    def build_data(self):
        """
        Builds deformer data
        """

        from tpDcc.dccs.maya.data import mesh
        from tpDcc.dccs.maya.core import deformer

        if not self._deformer:
            return

        if not deformer.is_deformer(deformer=self._deformer):
            raise Exception(
                'Object {} is not a valid deformer! Unable to instantiate MayaDeformerData() class object!'.format(
                    self._deformer))

        timer = cmds.timerX()

        attr_value_list = copy.deepcopy(self._data['attrValueList'])
        attr_connection_list = copy.deepcopy(self._data['attrConnectionList'])
        self.reset()
        self._data['attrValueList'] = copy.deepcopy(attr_value_list)
        self._data['attrConnectionList'] = copy.deepcopy(attr_connection_list)

        self._data['name'] = self._deformer
        self._data['type'] = cmds.objectType(self._deformer)

        affected_geo = deformer.get_affected_geometry(self._deformer, return_shapes=False)
        self._data['affectedGeometry'] = [str(i) for i in python.get_dict_ordered_keys_from_values(affected_geo)]

        # Build data for each affected geometry
        for geo in self._data['affectedGeometry']:
            geo_shape = cmds.listRelatives(geo, s=True, ni=True, pa=True)[0]
            self._data[geo] = dict()
            self._data[geo]['index'] = affected_geo[geo]
            self._data[geo]['geometryTypej'] = str(cmds.objectType(geo_shape))
            self._data[geo]['membership'] = deformer.get_deformer_set_member_indices(
                deformer=self._deformer, geometry=geo)
            self._data[geo]['weights'] = deformer.get_weights(deformer=self._deformer, geometry=geo)

            if self._data[geo]['geometryType'] == 'mesh':
                self._data[geo]['mesh'] = mesh.MeshData(geo)

        # Add custom data
        self.custom_deformer_attributes(self._data['type'])
        self.get_deformer_attr_values()
        self.get_deformer_attr_connections()

        build_time = cmds.timerX(st=timer)
        LOGGER.debug('MayaDeformerData: Data build time for "{}" : "{}"'.format(self._deformer, str(build_time)))

        return self._deformer

    def get_deformer_attr_values(self):
        """
        Get deformer attribute values based on the given deformer attribute list
        """

        deformer = self._data['name']
        for attr in self._data['attrValueList']:
            if not cmds.getAttr(deformer + '.' + attr, se=True) and cmds.listConnections(
                    deformer + '.' + attr, s=True, d=False):
                self._data['attrConnectionList'].append(attr)
            else:
                self._data['attrValueDict'][attr] = cmds.getAttr(deformer + '.' + attr)

    def get_deformer_attr_connections(self):
        """
        Get custom deformer attribute connections based on the given deformer connection list
        """

        deformer = self._data['name']
        for attr in self._data['attrConnectionList']:
            attr_cnt = cmds.listConnections(
                deformer + '.' + attr, s=True, d=False, p=True, sh=True, skipConversionNodes=True)
            if attr_cnt:
                self._data['attrConnectionDict'][attr] = attr_cnt[0]

    def custom_deformer_attributes(self, deformer_type):
        """
        Add custom attributes to data dictonary depending of the deformer type
        :param deformer_type: str
        """

        if deformer_type == 'curveTwist':
            self._data['attrValueList'].append('twistAngle')
            self._data['attrValueList'].append('twistType')
            self._data['attrValueList'].append('twistAxis')
            self._data['attrValueList'].append('distance')
            self._data['attrValueList'].append('scale')
            self._data['attrConnectionList'].append('twistCurve')
        elif deformer_type == 'directionalSmooth':
            self._data['attrValueList'].append('iterations')
            self._data['attrValueList'].append('smoothFactor')
            self._data['attrValueList'].append('smoothMethod')
            self._data['attrValueList'].append('maintainBoundary')
            self._data['attrValueList'].append('maintainDetail')
            self._data['attrValueList'].append('dentRemoval')
            self._data['attrValueList'].append('averageNormal')
            self._data['attrValueList'].append('weightU')
            self._data['attrValueList'].append('weightV')
            self._data['attrValueList'].append('weightN')
            self._data['attrValueList'].append('useReferenceUVs')
            self._data['attrConnectionList'].append('referenceMesh')
        elif deformer_type == 'strainRelaxer':
            self._data['attrValueList'].append('iterations')
            self._data['attrValueList'].append('bias')
            self._data['attrConnectionList'].append('refMesh')
        else:
            pass
