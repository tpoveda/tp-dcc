import maya.mel as mel

from tp.maya.cmds.modeling import create


def create_polygon_sphere_match():
	"""
	Creates a polygon sphere and matches to the current selected object.
	"""

	create.create_primitive_and_match('sphere')


def create_polygon_cube_match():
	"""
	Creates a polygon cube and matches to the current selected object.
	"""

	create.create_primitive_and_match('cube')


def create_polygon_cylinder_match():
	"""
	Creates a polygon cylinder and matches to the current selected object.
	"""

	create.create_primitive_and_match('cylinder')


def create_polygon_plane_match():
	"""
	Creates a polygon plane and matches to the current selected object.
	"""

	create.create_primitive_and_match('plane')


def create_polygon_torus_match():
	"""
	Creates a polygon torus and matches to the current selected object.
	"""

	create.create_primitive_and_match('torus')


def create_polygon_cone_match():
	"""
	Creates a polygon cone and matches to the current selected object.
	"""

	create.create_primitive_and_match('cone')


def create_polygon_disk_match():
	"""
	Creates a polygon disk and matches to the current selected object.
	"""

	create.create_primitive_and_match('disk')


def create_polygon_pyramid_match():
	"""
	Creates a polygon pyramid and matches to the current selected object.
	"""

	create.create_primitive_and_match('pyramid')


def create_polygon_pipe_match():
	"""
	Creates a polygon pipe and matches to the current selected object.
	"""

	create.create_primitive_and_match('pipe')


def create_polygon_prism_match():
	"""
	Creates a polygon prism and matches to the current selected object.
	"""

	create.create_primitive_and_match('prism')


def create_polygon_helix_match():
	"""
	Creates a polygon helix and matches to the current selected object.
	"""

	create.create_primitive_and_match('helix')


def create_polygon_gear_match():
	"""
	Creates a polygon gear and matches to the current selected object.
	"""

	create.create_primitive_and_match('gear')


def create_polygon_soccer_ball_match():
	"""
	Creates a polygon soccer ball and matches to the current selected object.
	"""

	create.create_primitive_and_match('soccerBall')


def create_polygon_platonic_solid_match():
	"""
	Creates a polygon platonic solid and matches to the current selected object.
	"""

	create.create_primitive_and_match('platonicSolid')


def create_polygon_super_ellipse_match():
	"""
	Creates a polygon super ellipse and matches to the current selected object.
	"""

	create.create_primitive_and_match('superEllipsoid')


def create_polygon_spherical_harmonics_match():
	"""
	Creates a polygon spherical harmonics and matches to the current selected object.
	"""

	create.create_primitive_and_match('sphericalHarmonics')


def create_polygon_ultra_shape_match():
	"""
	Creates a polygon ultra shape and matches to the current selected object.
	"""

	create.create_primitive_and_match('ultraShape')


def create_polygon_faces():
	"""
	Opens tool that allows to create a new polygon.
	"""

	mel.eval('setToolTo polyCreateFacetContext ; polyCreateFacetCtx -e -pc `optionVar -q polyKeepFacetsPlanar` polyCreateFacetContext')


def create_sweep_mesh():
	"""
	Creates a polygon cube along a curve that can be later edited. A curve must be selected.
	"""

	mel.eval('CreateSweepMesh')


def create_polygon_type():
	"""
	Creates a polygon type (text).
	"""

	mel.eval('CreatePolygonType')


def create_polygon_svg():
	"""
	Creates a polygon prism and matches to the current selected object.
	"""

	mel.eval('CreatePolygonSVG')
