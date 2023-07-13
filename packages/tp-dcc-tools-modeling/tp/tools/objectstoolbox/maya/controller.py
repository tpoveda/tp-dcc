from __future__ import annotations

from tp.core import log
from tp.maya.cmds import hotkeys

from tp.tools.objectstoolbox import controller

logger = log.modelLogger


class MayaObjectsToolboxController(controller.ObjectsToolboxController):

	def create_polygon_sphere(self):
		hotkeys.create_polygon_sphere_match()

	def create_polygon_cube(self):
		hotkeys.create_polygon_cube_match()

	def create_polygon_cylinder(self):
		hotkeys.create_polygon_cylinder_match()

	def create_polygon_plane(self):
		hotkeys.create_polygon_plane_match()

	def create_polygon_torus(self):
		hotkeys.create_polygon_torus_match()

	def create_polygon_cone(self):
		hotkeys.create_polygon_cone_match()

	def create_polygon_disk(self):
		hotkeys.create_polygon_disk_match()

	def create_polygon_pyramid(self):
		hotkeys.create_polygon_pyramid_match()

	def create_polygon_pipe(self):
		hotkeys.create_polygon_pipe_match()

	def create_polygon_prism(self):
		hotkeys.create_polygon_prism_match()

	def create_polygon_helix(self):
		hotkeys.create_polygon_helix_match()

	def create_polygon_gear(self):
		hotkeys.create_polygon_gear_match()

	def create_polygon_soccer_ball(self):
		hotkeys.create_polygon_soccer_ball_match()

	def create_polygon_platonic_solid(self):
		hotkeys.create_polygon_platonic_solid_match()

	def create_polygon_super_ellipse(self):
		hotkeys.create_polygon_super_ellipse_match()

	def create_polygon_spherical_harmonics(self):
		hotkeys.create_polygon_spherical_harmonics_match()

	def create_polygon_ultra_shape(self):
		hotkeys.create_polygon_ultra_shape_match()

	def create_polygon_faces(self):
		hotkeys.create_polygon_faces()

	def create_sweep_mesh(self):
		hotkeys.create_sweep_mesh()

	def create_polygon_type(self):
		hotkeys.create_polygon_type()

	def create_polygon_svg(self):
		hotkeys.create_polygon_svg()
