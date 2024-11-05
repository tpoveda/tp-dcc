from __future__ import annotations

from maya.api import OpenMaya

from . import constants, contexts


# MMatrix class for representing 4x4 transformation matrices.
Matrix = OpenMaya.MMatrix

# MTransformationMatrix class for representing and manipulating transformations.
TransformationMatrix = OpenMaya.MTransformationMatrix

# MVector class for representing 3D vectors.
Vector = OpenMaya.MVector

# MPoint.
Point = OpenMaya.MPoint

# MQuaternion class for representing quaternions.
Quaternion = OpenMaya.MQuaternion

# MEulerRotation class for representing rotations using Euler angles.
EulerRotation = OpenMaya.MEulerRotation
Angle = OpenMaya.MAngle
Distance = OpenMaya.MDistance

# MPlane class for representing planes.
Plane = OpenMaya.MPlane

# MTime class for representing time values.
Time = OpenMaya.MTime

# Constant representing a transform node type.
kTransform = OpenMaya.MFn.kTransform

# Constant representing a dependency node type.
kDependencyNode = OpenMaya.MFn.kDependencyNode

# Constant representing a DAG node type.
kDagNode = OpenMaya.MFn.kDagNode

# Constant representing a controller tag node type.
kControllerTag = OpenMaya.MFn.kControllerTag

# Constant representing a joint node type.
kJoint = OpenMaya.MFn.kJoint

# Constant representing world space.
kWorldSpace = OpenMaya.MSpace.kWorld

# Constant representing transform space.
kTransformSpace = OpenMaya.MSpace.kTransform

# Constant representing object space.
kObjectSpace = OpenMaya.MSpace.kObject

# MDGModifier class for modifying the DAG or DG.
dgModifier = OpenMaya.MDGModifier

# MDagModifier class for modifying the DAG.
dagModifier = OpenMaya.MDagModifier

# MDGContext class for representing the evaluation context of the DG.
DGContext = OpenMaya.MDGContext

# Namespace context object for manipulating namespaces.
namespaceContext = contexts.namespace_context

# Temporary namespace context object for creating and deleting namespaces.
tempNamespaceContext = contexts.temp_namespace_context

# Constant representing the XYZ rotate order.
kRotateOrder_XYZ = constants.kRotateOrder_XYZ

# Constant representing the YZX rotate order.
kRotateOrder_YZX = constants.kRotateOrder_YZX

# Constant representing the ZXY rotate order.
kRotateOrder_ZXY = constants.kRotateOrder_ZXY

# Constant representing the XZY rotate order.
kRotateOrder_XZY = constants.kRotateOrder_XZY

# Constant representing the YXZ rotate order.
kRotateOrder_YXZ = constants.kRotateOrder_YXZ

# Constant representing the ZYX rotate order.
kRotateOrder_ZYX = constants.kRotateOrder_ZYX

# Module containing constants representing different node types in Maya.
kNodeTypes = OpenMaya.MFn
