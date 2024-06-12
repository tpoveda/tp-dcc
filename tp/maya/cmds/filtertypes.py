from __future__ import annotations

ALL_FILTER_TYPE = 'All Node Types'
GROUP_FILTER_TYPE = 'Group'
GEOMETRY_FILTER_TYPE = 'Geometry'
POLYGON_FILTER_TYPE = 'Polygon'
SPHERE_FILTER_TYPE = 'Sphere'
BOX_FILTER_TYPE = 'Box'
CYLINDER_FILTER_TYPE = 'Cylinder'
CAPSULE_FILTER_TYPE = 'Capsule'
NURBS_FILTER_TYPE = 'Nurbs'
JOINT_FILTER_TYPE = 'Joint'
CURVE_FILTER_TYPE = 'Curve'
CIRCLE_FILTER_TYPE = 'Circle'
LOCATOR_FILTER_TYPE = 'Locator'
LIGHT_FILTER_TYPE = 'Light'
CAMERA_FILTER_TYPE = 'Camera'
CLUSTER_FILTER_TYPE = 'Cluster'
FOLLICLE_FILTER_TYPE = 'Follicle'
DEFORMER_FILTER_TYPE = 'Deformer'
TRANSFORM_FILTER_TYPE = 'Transform'
CONTROLLER_FILTER_TYPE = 'Controller'
PARTICLE_FILTER_TYPE = 'Particle'
NETWORK_FILTER_TYPE = 'Network'

# Dictionary containing that maps all filter nice names with their types.
TYPE_FILTERS = {
    ALL_FILTER_TYPE: 'All',
    GROUP_FILTER_TYPE: 'Group',
    GEOMETRY_FILTER_TYPE: ['mesh', 'nurbsSurface'],
    POLYGON_FILTER_TYPE: ['polygon'],
    SPHERE_FILTER_TYPE: ['sphere'],
    BOX_FILTER_TYPE: ['box'],
    CYLINDER_FILTER_TYPE: ['cylinder'],
    CAPSULE_FILTER_TYPE: ['capsule'],
    NURBS_FILTER_TYPE: ['nurbsSurface'],
    JOINT_FILTER_TYPE: ['joint'],
    CURVE_FILTER_TYPE: ['nurbsCurve'],
    CIRCLE_FILTER_TYPE: ['circle'],
    LOCATOR_FILTER_TYPE: ['locator'],
    LIGHT_FILTER_TYPE: ['light'],
    CAMERA_FILTER_TYPE: ['camera'],
    CLUSTER_FILTER_TYPE: ['cluster'],
    FOLLICLE_FILTER_TYPE: ['follicle'],
    DEFORMER_FILTER_TYPE: [
        'clusterHandle', 'baseLattice', 'lattice', 'softMod', 'deformBend', 'sculpt', 'deformTwist', 'deformWave',
        'deformFlare'],
    TRANSFORM_FILTER_TYPE: ['transform'],
    CONTROLLER_FILTER_TYPE: ['control'],
    PARTICLE_FILTER_TYPE: ['particle'],
    NETWORK_FILTER_TYPE: ['network']
}
