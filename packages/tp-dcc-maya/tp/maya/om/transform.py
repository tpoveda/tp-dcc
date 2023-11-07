from __future__ import annotations

import maya.api.OpenMaya as OpenMaya

from tp.maya.om import dagpath


def world_matrix(
        node: str | OpenMaya.MObject | OpenMaya.MDagPath,
        as_transformation_matrix: bool = False) -> OpenMaya.MMatrix | OpenMaya.MTransformationMatrix:
    """
    Returns the world matrix for the given node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get world matrix of.
    :param bool as_transformation_matrix: whether to return world matrix as matrix or a transformation matrix.
    :return: world matrix.
    :rtype: OpenMaya.MMatrix or OpenMaya.MTransformationMatrix
    """

    dag_path = dagpath.dag_path(node)
    fn_dag_node = OpenMaya.MFnDagNode(dag_path)
    plug = fn_dag_node.findPlug('worldMatrix', True)
    element = plug.elementByLogicalIndex(dag_path.instanceNumber()).asMObject()

    return transform_data(element) if as_transformation_matrix else matrix_data(element)


def matrix_data(matrix_node: OpenMaya.MObject) -> OpenMaya.MMatrix:
    """
    Converts the given OpenMaya.MObject to an OpenMaya.MMatrix.

    :param OpenMaya.MObject matrix_node: Maya object to convert.
    :return: Maya matrix object.
    :rtype: OpenMaya.MMatrix
    """

    if isinstance(matrix_node, OpenMaya.MMatrix):
        return matrix_node

    fn_matrix_data = OpenMaya.MFnMatrixData(matrix_node)
    if fn_matrix_data.isTransformation():
        return fn_matrix_data.transformation().asMatrix()

    return fn_matrix_data.matrix()


def transform_data(matrix_node: OpenMaya.MObject) -> OpenMaya.MTransformationMatrix:
    """
    Converts the given OpenMaya.MObject to an OpenMaya.MTransformationMatrix.

    :param OpenMaya.MObject matrix_node: Maya object to convert.
    :return: Maya transformation matrix object.
    :rtype: OpenMaya.MTransformationMatrix
    """

    if isinstance(matrix_node, OpenMaya.MTransformationMatrix):
        return matrix_node

    fn_matrix_data = OpenMaya.MFnMatrixData(matrix_node)
    if fn_matrix_data.isTransformation():
        return fn_matrix_data.transformation()

    return OpenMaya.MTransformationMatrix(fn_matrix_data.matrix())
