from __future__ import annotations

from tp.core import log
from tp.common.qt import api as qt

logger = log.modelLogger


class ObjectsToolboxController(qt.QObject):

	def create_polygon_sphere(self):
		"""
		Creates a polygon sphere and matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_cube(self):
		"""
		Creates a polygon cube and matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_cylinder(self):
		"""
		Creates a polygon cylinder and matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_plane(self):
		"""
		Creates a polygon plane and matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_torus(self):
		"""
		Creates a polygon torus and matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_cone(self):
		"""
		Creates a polygon cone and matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_disk(self):
		"""
		Creates a polygon disk that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_pyramid(self):
		"""
		Creates a polygon pyramid that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_pipe(self):
		"""
		Creates a polygon pipe that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_prism(self):
		"""
		Creates a polygon prism that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_helix(self):
		"""
		Creates a polygon helix that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_gear(self):
		"""
		Creates a polygon gear that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_soccer_ball(self):
		"""
		Creates a polygon soccer ball that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_platonic_solid(self):
		"""
		Creates a polygon platonic solid that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_super_ellipse(self):
		"""
		Creates a polygon super ellipse that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_spherical_harmonics(self):
		"""
		Creates a polygon spherical harmonics that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_ultra_shape(self):
		"""
		Creates a polygon ultra shape that matches to the current selected object.
		"""

		raise NotImplementedError

	def create_polygon_faces(self):
		"""
		Opens tool that allows to create a new polygon.
		"""

		raise NotImplementedError

	def create_sweep_mesh(self):
		"""
		Creates a polygon cube along a curve that can be later edited. A curve must be selected.
		"""

		raise NotImplementedError

	def create_polygon_type(self):
		"""
		Creates a polygon type (text).
		"""

		raise NotImplementedError

	def create_polygon_svg(self):
		"""
		Creates a polygon SVG that matches to the current selected object.
		"""

		raise NotImplementedError
