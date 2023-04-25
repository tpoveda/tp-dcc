#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module include data class for blendshapes
"""

import string

import maya.cmds

from tp.core import log
from tp.common.python import helpers, name as core_name
from tp.maya.cmds import exceptions, deformer, shape, component, name as name_utils, attribute as attr_utils
from tp.maya.cmds import geometry as geo_utils

logger = log.tpLogger


class BlendShapeOrigin(object):
    Local = 'local'
    World = 'world'


class BlendShapeDeformerOrder(object):
    After = 'after'
    Before = 'before'
    Parallel = 'parallel'
    Split = 'split'
    Foc = 'foc'


class BlendShapeTarget(object):
    def __init__(self, alias, index):
        self._name = alias
        self._index = index
        self._connection = None
        self._value = 0

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def alias(self):
        return self._name

    @alias.setter
    def alias(self, value):
        self._name = value

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class BlendShape(object):
    def __init__(self, blendshape_name):
        self._blendshape = blendshape_name
        self._meshes = list()
        self._targets = dict()
        self._targets_list = list()
        self._weight_indices = list()
        self._mesh_index = 0
        self._prune_compare_mesh = None
        self._prune_distance = -1

    def create(self, mesh, front_of_chain=True):
        """
        Creates an empty deformer on the given mesh
        :param mesh: str, the name of a mesh transform
        :return: str, newly created blendshape
        """

        new_blendshape = maya.cmds.deformer(mesh, type='blendShape', frontOfChain=front_of_chain)[0]
        mesh_name = name_utils.get_basename(mesh)
        if not self._blendshape:
            base_mesh_name = name_utils.get_basename(mesh_name, remove_namespace=True)
            new_name = 'blendshape_{}'.format(base_mesh_name)
            self._blendshape = maya.cmds.rename(new_blendshape, new_name)

        self._store_targets()
        self._store_meshes()

        return new_blendshape

    def set(self, blendshape_node):
        """
        Sets the blendshape node to work on
        :param blendshape_node: str
        """

        self._blendshape = blendshape_node
        self._store_targets()
        self._store_meshes()

    def rename(self, new_name):
        """
        Returns wrapped blendshape node
        :param new_name: str, new name of the blendshape
        """

        self._blendshape = maya.cmds.rename(self._blendshape, new_name)
        self.set(self._blendshape)

    def set_envelope(self, value):
        """
        Sets the envelope value of the blendshape node
        :param value: float
        """

        maya.cmds.setAttr('{}.envelope'.format(self._blendshape), value)

    def get_mesh_index(self, mesh):
        # TODO: Finish
        meshes = maya.cmds.blendShape(self._blendshape, query=True, geometry=True)
        raise NotImplementedError()

    def set_mesh_index(self, index):
        self._mesh_index = index

    def get_mesh_count(self):
        """
        Returns the total meshes of the wrapped blendshape node
        :return: int
        """

        meshes = maya.cmds.blendShape(self._blendshape, query=True, geometry=True)
        self._meshes = meshes

        return len(meshes)

    def set_prune_distance(self, distance, comparison_mesh):
        self._prune_distance = distance
        self._prune_compare_mesh = comparison_mesh

    def is_target(self, target_name):
        """
        Returns whether given node is a target of the wrapped blendshape node
        :param target_name: str
        :return: bool
        """

        if not self._targets:
            self._store_targets()

        target_name = name_utils.get_basename(target_name)

        return target_name in self._targets

    def is_target_connected(self, target_name):
        target_attr = self._get_target_attribute(target_name)
        input_value = attr_utils.attribute_input(target_attr)
        if input_value:
            return True

        return False

    def get_target_names(self):
        if not self._targets:
            self._store_targets()

        return self._targets_list

    def get_weights(self, target_name=None, mesh_index=0):
        weights = list()

        if not self._meshes:
            self._store_meshes()
        if not self._meshes:
            return weights

        mesh = self._meshes[mesh_index]
        vertex_count = component.get_component_count(mesh)

        if target_name is None:
            for i in range(vertex_count):
                weight_attr = self._get_input_target_base_weights_attribute(mesh_index)
                weight = maya.cmds.getAttr('{}[{}]'.format(weight_attr, i))
                weights.append(weight)
        else:
            for i in range(vertex_count):
                weight_attr = self._get_input_target_group_weights_attribute(mesh_index)
                weight = maya.cmds.getAttr('{}[{}]'.format(weight_attr, i))
                weights.append(weight)

        return weights

    def set_weights(self, weights, target_name=None, mesh_index=0):
        """
        Sets the vertex weights on the wrapped blendShape node. If no target name is given, base weights are set.
        :param weights: list(float), list of weight values. If a float is given, the float will be converted into a
            list of the same float with the same number of vertices.
        :param target_name: str, name of the target. If not given, base weights will be set.
        :param mesh_index: int, the index of the mesh in the wrapped blendShape node.
        """

        weights = helpers.force_list(weights)
        weight_count = len(weights)

        if weight_count == 1:
            if not self._meshes:
                self._store_meshes()
            if not self._meshes:
                return False
            mesh = self._meshes[mesh_index]
            vertex_count = component.get_component_count(mesh)
            weights = weights * vertex_count

        if target_name:
            attribute = self._get_input_target_group_weights_attribute(target_name, mesh_index=mesh_index)
        else:
            attribute = self._get_input_target_base_weights_attribute(mesh_index=mesh_index)

        # TODO: Check whether this can be done faster using Maya API
        """
        plug = api.get_plug(attribute)
        for i in range(weight_count):
            plug.elementByLogicalIndex(inc).setFloat(weights[inc])
        """

        try:
            maya.cmds.setAttr(attribute + '[*}', *weights)
        except Exception:
            for i in range(weight_count):
                attribute_name = attribute + '[{}]'.format(i)
                maya.cmds.setAttr(attribute_name, weights[i])

        return True

    def _get_input_target(self, mesh_index=0):
        attribute = [self._blendshape, 'inputTarget[{}]'.format(mesh_index)]
        attribute = string.join(attribute, '.')

        return attribute

    def _get_input_target_group(self, name, mesh_index=0):
        if not self._targets:
            self._store_targets()
        if not self._targets or name not in self._targets:
            return

        target_index = self._targets[name].index
        input_attribute = self._get_input_target(mesh_index)
        attribute = [input_attribute, 'inputTargetGroup[{}]'.format(target_index)]
        attribute = string.join(attribute, '.')

        return attribute

    def _get_input_target_base_weights_attribute(self, mesh_index=0):
        input_attribute = self._get_input_target(mesh_index)
        attribute = [input_attribute, 'baseWeights']
        attribute = string.join(attribute, '.')

        return attribute

    def _get_input_target_group_weights_attribute(self, name, mesh_index=0):
        input_attribute = self._get_input_target_group(name, mesh_index=mesh_index)
        attribute = [input_attribute, 'targetWeights']
        attribute = string.join(attribute, '.')

        return attribute

    def _store_target(self, alias, index):
        target = BlendShapeTarget(alias, index)
        self._targets[alias] = target
        self._targets_list.append(alias)
        self._weight_indices.append(index)
        self._weight_indices.sort()

    def _store_targets(self):
        if not self._blendshape:
            return

        target_attrs = list()
        if maya.cmds.objExists(self._get_input_target(0)):
            target_attrs = maya.cmds.listAttr(self._get_input_target(0), multi=True)
        if not target_attrs:
            return

        alias_index_map = map_blend_target_alias_to_index(self._blendshape)
        if not alias_index_map:
            return

        for index, alias in alias_index_map.items():
            self._store_target(alias, index)

    def _store_meshes(self):
        if not self._blendshape:
            return

        self._meshes = maya.cmds.deformer(self._blendshape, query=True, geometry=True)

    def _get_target_attribute(self, target_name):
        return '{}.{}'.format(self._blendshape, target_name)


def check_blendshape(blend_shape):
    """
    Check sif a node is a valid blendshape and raise an exception if the blenshape is not valid
    :param blend_shape: str, name of the node to be checked
    :return: bool, True if the given node is a blendshape node
    """

    if not is_blendshape(blend_shape):
        raise exceptions.BlendShapeExistsException(blend_shape)


def is_blendshape(blend_shape):
    """
    Checks if the given object is a blend shape
    :param blend_shape: str, object to query
    :return: bool, True if the given node is a blend shape node
    """

    if not maya.cmds.objExists(blend_shape):
        return False

    if not maya.cmds.objectType(blend_shape) == 'blendShape':
        return False

    return True


def get_base_geo(blend_shape):
    """
    Get list of blendShape base geometry
    :param blend_shape: str, blendshape to get base geometry from
    :return: list<str>
    """

    check_blendshape(blend_shape)

    base_geo = deformer.get_affected_geometry(deformer=blend_shape)
    base_geo_list = zip(base_geo.values(), base_geo.keys())
    base_geo_list.sort()
    base_geo_list = [i[1] for i in base_geo_list]

    return base_geo_list


def has_base(blend_shape, base):
    """
    Check if the given blendshape has a specific base geometry
    :param blend_shape: str, blendshape node to query
    :param base: str, base geometry to query
    :return: bool
    """

    check_blendshape(blend_shape)

    return base in get_base_geo(blend_shape)


def get_base_index(blend_shape, base):
    """
    Returns the blendshape input geometry index for the given base geometry
    :param blend_shape: str, blendshape to get base geometry index from
    :param base: str, base geometry to get the input geometry index for
    :return: str
    """

    check_blendshape(blend_shape)
    if not has_base(blend_shape, base):
        raise exceptions.BlendShapeBaseGeometryException(base=base, blendshape=blend_shape)

    base_geo = deformer.get_affected_geometry(blend_shape)
    if base not in base_geo:
        raise exceptions.BlendShapeBaseIndexException(base=base, blendshape=blend_shape)

    return base_geo[base]


def has_target(blend_shape, target):
    """
    Checks if the given target exist on the given blendshape node
    :param blend_shape: str, name of blendshape to query
    :param target: str, blendshape target to query
    :return: str
    """

    check_blendshape(blend_shape)

    return target in get_target_list(blend_shape)


def has_target_geo(blend_shape, target, base=''):
    """
    Check if the given blendshape target has live target geometry
    :param blend_shape: str, name of blendshape to query
    :param target: str, blendshape target to query
    :param base: str, base geometry index to check for live target geometry
    :return: str
    """

    check_blendshape(blend_shape)
    if target not in get_target_list(blend_shape):
        raise Exception('BlendShape "{}" has no target "{}"!'.format(blend_shape, target))

    target_geo = get_target_geo(blend_shape, target, base_geo=base)

    return bool(target_geo)


def get_target_index(blend_shape, target):
    """
    Get the target index of the given blendShape and target name
    :param blend_shape: str, name of blendshape to get target index for
    :param target: blendshape target to get the index for
    :return: str
    """

    check_blendshape(blend_shape)
    if not maya.cmds.objExists(blend_shape + '.' + target):
        raise Exception('BlendShape "{}" has no target "{}"!'.format(blend_shape, target))

    alias_list = maya.cmds.aliasAttr(blend_shape, query=True)
    alias_index = alias_list.index(target)
    alias_attr = alias_list[alias_index + 1]

    target_index = int(alias_attr.split('[')[-1].split(']')[0])

    return target_index


def get_target_geo(blend_shape, target, base_geo=''):
    """
    Get the connected target geometry given a blendshape and target
    :param blend_shape: str, blendshape node to get target geometry from
    :param target: str, blendshape target to get source geometry from
    :param base_geo: str, base geometry of the blendshaspe to get the target geometry for. If empty, use base geometry
        at index 0
    :return: str
    """

    target_index = get_target_index(blend_shape, target)
    geo_index = 0
    if base_geo:
        geo_index = deformer.get_geo_index(base_geo, blend_shape)

    # Get weight index
    # NOTE: Hardcoded to check inputTargetItem 6000
    # TODO: Instead, we should check all existing multi indexes
    weight_index = 6000

    target_geo_attr = blend_shape + '.inputTarget[' + str(geo_index) + '].inputTargetGroup[' + str(
        target_index) + '].inputTargetItem[' + str(weight_index) + '].inputGeomTarget'
    target_geo_cnt = maya.cmds.listConnections(target_geo_attr, s=True, d=False)
    if not target_geo_cnt:
        target_geo_cnt = ['']

    return target_geo_cnt


def get_target_list(blend_shape):
    """
    Returns the target list for the given blendshape
    :param blend_shape: str, name of blendshape to get target list for
    :return: list<str>
    """

    check_blendshape(blend_shape)

    target_list = maya.cmds.listAttr(blend_shape + '.w', m=True)
    if not target_list:
        target_list = list()

    return target_list


def get_target_geo_list(blend_shape, base_geo=''):
    """
    Get the list of connected target geometry to the given blendshape
    :param blend_shape: str, blendshape node to get target geometry list from
    :param base_geo: str, base geometry of the blendshape to get the target geometry for. If empty, uses base geometry
        at index 0
    :return: list<str>
    """

    target_list = get_target_list(blend_shape)
    target_geo_list = list()
    for target in target_list:
        target_geo = get_target_geo(blend_shape, target, base_geo)
        target_geo_list.append(target_geo)

    return target_geo_list


def get_target_name(blend_shape, target_geo):
    """
    Get blendShape target alias for the given target geometry
    :param blend_shape: str, blendshape node to get target name from
    :param target_geo: str, blendshape target geometry to get alias name for
    :return: str
    """

    check_blendshape(blend_shape)
    if not maya.cmds.objExists(target_geo):
        raise Exception('Target geometry "{}" does not exists!'.format(target_geo))

    # Get target shapes
    target_shape = shape.get_shapes(node_name=target_geo, non_intermediates=True, intermediates=False)
    if not target_shape:
        target_shape = maya.cmds.ls(maya.cmds.listRelatives(
            target_geo, ad=True, pa=True), shapes=True, noIntermediate=True)
    if not target_shape:
        raise Exception('No shapes found under target geometry "{}"!'.format(target_geo))

    # Find target connection
    target_cnt = maya.cmds.listConnections(target_shape, sh=True, d=True, s=False, p=False, c=True)
    if not target_cnt.count(blend_shape):
        raise Exception('Target geometry "{}" is not connected to blendShape "{}"!'.format(target_geo, blend_shape))
    target_cnt_index = target_cnt.index(blend_shape)
    target_cnt_attr = target_cnt[target_cnt_index - 1]
    target_cnt_plug = maya.cmds.listConnections(target_cnt_attr, sh=True, p=True, d=True, s=False)[0]

    # Get target index and alias
    target_index = int(target_cnt_plug.split('.')[2].split('[')[1].split(']')[0])
    target_alias = maya.cmds.aliasAttr(blend_shape + '.weight[' + str(target_index) + ']', query=True)

    return target_alias


def next_available_target_index(blend_shape):
    """
    Get the next available blendshape target index
    :param blend_shape: str, name of blendshape to get next available target index for
    :return: str
    """

    check_blendshape(blend_shape)

    target_list = get_target_list(blend_shape)
    if not target_list:
        return 0

    last_index = get_target_index(blend_shape, target_list[-1])
    next_index = last_index + 1

    return next_index


def add_empty_target(blend_shape, target_alias='', input_target_items=None):
    """
    Adds a new empty target into the given blendShape node
    :param blend_shape: str, name of the blendShape to add target to
    :param target_alias: str, override the default blendShape target alias
    :param input_target_items:
    :return: str
    """

    if not target_alias:
        target_name = 'newEmptyTarget'
    else:
        target_name = target_alias

    check_blendshape(blend_shape)
    next_index = next_available_target_index(blend_shape)
    out_geo = maya.cmds.getAttr(blend_shape + '.outputGeometry', multiIndices=True)
    for i in out_geo:
        maya.cmds.setAttr(
            '{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[6000].inputPointsTarget'.format(
                blend_shape, i, next_index), type='pointArray', *[0])
        if input_target_items:
            for iti in input_target_items:
                maya.cmds.setAttr(
                    '{}.inputTarget[{}].inputTargetGroup[{}].inputTargetItem[{}].inputPointsTarget'.format(
                        blend_shape, i, next_index, iti), type='pointArray', *[0])
    maya.cmds.setAttr('{}.w[{}]'.format(blend_shape, next_index), 0.0)
    maya.cmds.aliasAttr(target_name, '{}.w[{}]'.format(blend_shape, next_index))
    maya.cmds.refresh()

    return blend_shape + '.' + target_name


def add_target(blend_shape, target, base='', target_index=-1, target_alias='', target_weight=0.0, topology_check=True):
    """
    Adds a new target to the given blendShape
    :param blend_shape: str, name of the blendShape to add target to
    :param target: str, new blendshape target geometry
    :param base: str, blendsahpe base geometry, if empty, use first connected base geometry
    :param target_index: int, specify the target index, if less than 0, use next available index
    :param target_alias: str, override the default blendShape target alias
    :param target_weight: float, set the target weight value
    :param topology_check: bool, Whether to check the topology between target and base geometries
    :return: str
    """

    check_blendshape(blend_shape)
    if not maya.cmds.objExists(target):
        raise Exception('Target geometry "{}" does not exists!'.format(target))
    if base and not maya.cmds.objExists(base):
        raise Exception('Base geometry "{}" does not exists!'.format(base))

    if not base:
        base = get_base_geo(blend_shape)[0]
    if target_index < 0:
        target_index = next_available_target_index(blend_shape)

    maya.cmds.blendShape(blend_shape, e=True, t=(base, target_index, target, 1.0), topologyCheck=topology_check)

    target_name = get_target_name(blend_shape, target)
    if target_alias:
        target_index = get_target_index(blend_shape, target_name)
        maya.cmds.aliasAttr(target_alias, blend_shape + '.weight[' + str(target_index) + ']')
        target_name = target_alias

    if target_weight:
        maya.cmds.setAttr(blend_shape + '.' + target_name, target_weight)

    return blend_shape + '.' + target_name


def create(base_geo, target_geo=None, origin='local', deform_order=None, name=None):
    """
    Creates a blend shape deformer for the given base geometry
    :param base_geo: str, geometry to apply blend shape deformer to
    :param target_geo: list<str>, list of blend shape target models
    :param origin: BlendShapeOrigin, create a local or world space blendshape deformer
    :param deform_order: BlendShapeDeformerOrder, deform order
    :param name: str, blendshape node name
    :param target_weight: float, default target weight value
    :return: str
    """

    if not maya.cmds.objExists(base_geo):
        raise Exception('Base geometry "{}" does not exists!'.format(base_geo))

    if not name:
        name = '{}_blendShape'.format(base_geo.split(':')[-1])

    if is_blendshape(name):
        logger.debug('BlendShape {} already exists!'.format(name))
        return name

    if deform_order == BlendShapeDeformerOrder.After:
        blend_shape = maya.cmds.blendShape(base_geo, name=name, origin=origin, after=True)[0]
    elif deform_order == BlendShapeDeformerOrder.Before:
        blend_shape = maya.cmds.blendShape(base_geo, name=name, origin=origin, before=True)[0]
    elif deform_order == BlendShapeDeformerOrder.Parallel:
        blend_shape = maya.cmds.blendShape(base_geo, name=name, origin=origin, parallel=True)[0]
    elif deform_order == BlendShapeDeformerOrder.Split:
        blend_shape = maya.cmds.blendShape(base_geo, name=name, origin=origin, split=True)[0]
    elif deform_order == BlendShapeDeformerOrder.Foc:
        blend_shape = maya.cmds.blendShape(base_geo, name=name, origin=origin, foc=True)[0]
    else:
        blend_shape = maya.cmds.blendShape(base_geo, name=name, origin=origin)[0]

    target_geo = helpers.force_list(target_geo)
    for target in target_geo:
        add_target(blend_shape=blend_shape, target=target, base=base_geo)

    return blend_shape


def add_target_in_between(blend_shape, target_geo, target_name, base='', target_weight=0.5):
    """
    Adds a new target in between to the given blendshape target
    :param blend_shape: str, name of blendshape to add target from
    :param target_geo: str, new blendshape target inbetween geometry
    :param target_name: str, blendshape target name to add inbetween target to
    :param base: str, blendshape base geometry. If empty, use first connected base geometry
    :param target_weight: int, blendshape inbetween target weight value
    :return: str
    """

    check_blendshape(blend_shape)

    if not maya.cmds.objExists(target_geo):
        raise Exception('Target geometry "{}" does not exists!'.format(target_geo))
    if not has_target(blend_shape, target_name):
        raise Exception('BlendShape "{}" has no target "{}"!'.format(blend_shape, target_name))

    if base and not maya.cmds.objExists(base):
        raise Exception('Base geometry "{}" does not exists!'.format(base))

    if not base:
        base = get_base_geo(blend_shape)[0]
    target_index = get_target_index(blend_shape, target_name)
    maya.cmds.blendShape(blend_shape, e=True, t=(base, target_index, target_geo, target_weight))

    return blend_shape + '.' + target_name


def get_target_weights(blend_shape, target, geometry=''):
    """
    Get per vertex target weights for the given blendshape target
    :param blend_shape: str, name of blendshape to get target weights for
    :param target: str, name of blendshape target to get weights for
    :param geometry: str, name of blendshape driven geometry to get weights from
    :return: str
    """

    check_blendshape(blend_shape)
    if not maya.cmds.objExists(blend_shape + '.' + target):
        raise Exception('BlendShape "{}" has no "{}" target attribute!'.format(blend_shape, target))
    if geometry and not maya.cmds.objExists(geometry):
        raise Exception('Object "{}" does not exists!'.format(geometry))

    alias_list = maya.cmds.aliasAttr(blend_shape, query=True)
    alias_target = alias_list[(alias_list.index(target) + 1)]
    target_index = int(alias_target.split('[')[-1].split(']')[0])

    geo_index = 0
    if geometry:
        geo_index = deformer.get_geo_index(geometry, blend_shape)

    wt = maya.cmds.getAttr(blend_shape + '.it[' + str(geo_index) + '].itg[' + str(target_index) + '].tw')[0]

    return list(wt)


def set_target_weights(blend_shape, target, wt, geometry=''):
    """
    Set per vertex target weights for the given blendshape target
    :param blend_shape: str, name of blendshape to set target weights for
    :param target: str, name of blendshape target to set weights for
    :param wt: list<float>, weight value list to apply to the given blendshape target
    :param geometry: str, name of blendshape driven geometry to set weights on
    """

    check_blendshape(blend_shape)
    if not maya.cmds.objExists(blend_shape + '.' + target):
        raise Exception('BlendShape "{}" has no "{}" target attribute!'.format(blend_shape, target))

    geometry = geometry or get_base_geo(blend_shape)
    if geometry and not maya.cmds.objExists(geometry):
        raise Exception('Object "{}" does not exists!'.format(geometry))

    alias_list = maya.cmds.aliasAttr(blend_shape, query=True)
    alias_target = alias_list[(alias_list.index(target) + 1)]
    target_index = int(alias_target.split('[')[-1].split(']')[0])

    geo_index = 0
    if geometry:
        geo_index = deformer.get_geo_index(geometry, blend_shape)

    comp_count = component.get_component_count(geometry)

    maya.cmds.setAttr(
        blend_shape + '.it[' + str(geo_index) + '].itg[' + str(target_index) + '].tw[0:' + str(comp_count - 1) + ']',
        *wt)


def connect_to_target(blend_shape, target_geo, target_name, base_geo, weight=1.0, force=False):
    """
    Connects a new target to a given blendShape target
    :param blend_shape: str, name of blendshape to connect geometry target to
    :param target_geo: str, geometry to connect to blendshape target
    :param target_name: str, blendshape target name to connect geometry to
    :param base_geo: str, blendshape base geometry name
    :param weight: float, blendshape target weight value to connect geometry to
    :param force: bool, force connection
    """

    check_blendshape(blend_shape)
    if not has_target(blend_shape, target_name):
        raise exceptions.BlendShapeTargetException(blend_shape, target_name)
    if not maya.cmds.objExists(target_geo):
        raise Exception('Target geometry "{}" does not exists!'.format(target_geo))

    target_index = get_target_index(blend_shape, target_name)

    if force:
        geo_index = deformer.get_geo_index(base_geo, blend_shape)
        geo_shape = maya.cmds.listRelatives(target_geo, s=True, ni=True)
        if geo_shape:
            geo_shape = geo_shape[0]
            geo_type = maya.cmds.objectType(geo_shape)
        else:
            geo_shape = target_geo
            geo_type = 'none'

        # Get geometry type output attribute
        geo_dict = {'mesh': '.worldMesh[0]', 'nurbsSurface': '.worldSpace[0]', 'nurbsCurve': '.worldSpace[0]'}
        if geo_type in geo_dict:
            geo_attr = geo_dict[geo_type]
        else:
            geo_attr = ''

        weight_index = int(weight * 6000)

        maya.cmds.connectAttr(
            geo_shape + geo_attr, blend_shape + '.inputTarget[' + str(
                geo_index) + '].inputTargetGroup[' + str(target_index) + '].inputTargetItem[' + str(
                weight_index) + '].inputGeomTarget', f=True)
    else:
        if has_target(blend_shape, target_name) and weight != 1.0:
            # Connect geometry to target input as inbetween
            maya.cmds.blendShape(blend_shape, e=True, ib=True, t=[base_geo, target_index, target_geo, weight])
        else:
            # Connect geometry to target input
            maya.cmds.blendShape(blend_shape, e=True, t=[base_geo, target_index, target_geo, weight])


def rename_target(blend_shape, target, new_name):
    """
    Rename the given blendshape target
    :param blend_shape: str, name of blendshape to rename target from
    :param target: str, blenshape target to rename
    :param new_name: str, new name for the blendshpae target
    :return: str
    """

    check_blendshape(blend_shape)
    if not has_target(blend_shape, target):
        raise exceptions.BlendShapeTargetException(blend_shape, target)

    maya.cmds.aliasAttr(new_name, blend_shape + '.' + target)

    return new_name


def remove_target(blend_shape, target, base_geo):
    """
    Removes the given blendshape target
    :param blend_shape: str, name of blendshape to remove target from
    :param target: str, blendshape target to remove
    :param base_geo: str, blendshape base geometry name
    """

    check_blendshape(blend_shape)
    if not has_target(blend_shape, target):
        raise exceptions.BlendShapeTargetException(blend_shape, target)

    target_index = get_target_index(blend_shape, target)
    target_geo = get_target_geo(blend_shape, target, base_geo)
    if target_geo:
        target_geo = target_geo[0]

    if not target_geo:
        maya.cmds.setAttr(blend_shape + '.envelope', 0.0)
        target_geo = maya.cmds.duplicate(base_geo)[0]
        maya.cmds.setAttr(blend_shape + '.envelope', 1.0)
        connect_to_target(blend_shape, target_geo, target, base_geo, 1.0, force=True)

    maya.cmds.blendShape(blend_shape, e=True, rm=True, t=[base_geo, target_index, target_geo, 1.0])


def remove_unconnected_targets(blend_shape, base):
    """
    Remove unconnected blendshape targets
    :param blend_shape: str, blendshape deformer to operate on
    :param base: str, base geometry connected to the blendshape
    :return: list<str>, list of removed blendshape targets
    """

    check_blendshape(blend_shape)

    target_list = get_target_list(blend_shape)
    deleted_target_list = list()
    for target in target_list:
        target_cnt = maya.cmds.listConnections(blend_shape + '.' + target, s=True, d=False)
        if not target_cnt:
            try:
                remove_target(blend_shape, target, base)
            except Exception:
                logger.warning('Unable to delete blendshape target "{}"!'.format(target))
            else:
                logger.warning('Target "{}" deleted!')
                deleted_target_list.append(target)

    return deleted_target_list


def map_blend_target_alias_to_index(blendshape_node):
    """
    Returns the aliases for blendshape weight targets and the index of the target
    :param blendshape_node: str, name of the blendshape
    :return: dict(str, index), dict[alias] = target index
    """

    alias_map = dict()

    aliases = maya.cmds.aliasAttr(blendshape_node, query=True)
    if not aliases:
        return alias_map

    for i in range(0, len(aliases), 2):
        alias = aliases[i]
        weight = aliases[i + 1]
        target_index = core_name.get_end_number(weight)
        alias_map[alias] = target_index

    return alias_map


def map_blend_to_target_alias(blendshape_node):
    """
    Returns a map between the target index and its alias name on the given blendshape
    :param blendshape_node: str, name of the blendshape
    :return: dict(int, str), dict[target_index] = weight alias
    """

    alias_map = dict()

    aliases = maya.cmds.aliasAttr(blendshape_node, query=True)
    if not aliases:
        return alias_map

    for i in range(0, len(aliases), 2):
        alias = aliases[i]
        weight = aliases[i + 1]
        target_index = core_name.get_end_number(weight)
        alias_map[target_index] = alias

    return alias_map


def get_index_at_alias(alias, blendshape_node):
    """
    Returns corresponding target index from the given blendshape weight alias
    :param alias: str, name of the weight alias
    :param blendshape_node: str, name of the blendshape
    :return: int, corresponding target index to the alias
    """

    map_dict = map_blend_target_alias_to_index(blendshape_node)
    if not map_dict:
        return

    return map_dict.get(alias, None)


def is_mesh_blendshape_compatible(base, target):
    """
    Checks whether the given target mesh is compatible with base geometry (have same vertices, edges and face count)
    :param base: str
    :param target: str
    :return: bool
    """

    return geo_utils.is_mesh_compatible(base, target)
