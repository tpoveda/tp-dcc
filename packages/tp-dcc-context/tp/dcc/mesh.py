from tp.core import dcc

if dcc.is_maya():
    from tp.dcc.maya.mesh import MayaMesh as Mesh
elif dcc.is_max():
    from tp.dcc.max.mesh import MaxMesh as Mesh
elif dcc.is_standalone():
    from tp.dcc.standalone.mesh import StandaloneMesh as Mesh
else:
    raise ImportError(f'Unable to import DCC Mesh class for: {dcc.current_dcc()}')
