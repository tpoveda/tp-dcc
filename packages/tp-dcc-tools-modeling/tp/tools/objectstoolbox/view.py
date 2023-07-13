from __future__ import annotations

import typing
from typing import Dict

from tp.common.qt import api as qt

if typing:
	from tp.tools.objectstoolbox.controller import ObjectsToolboxController


def tooltips() -> Dict:

	return {
		'create_sphere': """
		Creates a Polygon Sphere. 
		Matches to the current selection, if there is a selection.
		
		Hotkey: None
		""",
		'create_cube': """
		Creates a Polygon Cube. 
		Matches to the current selection, if there is a selection.
	
		Hotkey: None
		""",
		'create_cylinder': """
		Creates a Polygon Cylinder. 
		Matches to the current selection, if there is a selection.
	
		Hotkey: None
		""",
		'create_plane': """
		Creates a Polygon Plane. 
		Matches to the current selection, if there is a selection.
	
		Hotkey: None
		""",
		'create_torus': """
		Creates a Polygon Torus. 
		Matches to the current selection, if there is a selection.
	
		Hotkey: None
		""",
		'create_cone': """
		Creates a Polygon Cone. 
		Matches to the current selection, if there is a selection.
	
		Hotkey: None
		""",
		'create_polygon': """
		Opens the Create Polygon Tool. 
		Click multiple times on the ground to create a new polygon.
	
		Hotkey: None
		""",
		'create_sweep_mesh': """
		Creates a tube along a curve that can be edited in the Attribute Editor.
		Select an existing curve, or nothing, and run.
	
		Hotkey: None
		""",
		'create_type': """
		Creates a Polygon Type (Text).
		Open the Attribute Editor to edit text.
	
		Hotkey: None
		"""
	}


class ObjectsToolboxView(qt.QWidget):
	def __init__(self, controller: ObjectsToolboxController, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._controller = controller
		self._tooltips = tooltips()

		self._setup_widgets()
		self._setup_layouts()
		self._setup_signals()

	def _setup_widgets(self):
		"""
		Internal function that setup view widgets.
		"""

		self._objects_collapsable = qt.CollapsableFrameThin('Objects', collapsed=False, parent=self)

		self._sphere_button = qt.left_aligned_button(
			'', icon=':polySphere', tooltip=self._tooltips['create_sphere'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._cube_button = qt.left_aligned_button(
			'', icon=':polyCube', tooltip=self._tooltips['create_cube'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._cylinder_button = qt.left_aligned_button(
			'', icon=':polyCylinder', tooltip=self._tooltips['create_cylinder'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._plane_button = qt.left_aligned_button(
			'', icon=':polyMesh', tooltip=self._tooltips['create_plane'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._torus_button = qt.left_aligned_button(
			'', icon=':polyTorus', tooltip=self._tooltips['create_torus'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._cone_button = qt.left_aligned_button(
			'', icon=':polyCone', tooltip=self._tooltips['create_cone'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._create_polygon_button = qt.left_aligned_button(
			'', icon=':polyCreateFacet', tooltip=self._tooltips['create_polygon'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._create_sweep_mesh_button = qt.left_aligned_button(
			'', icon='sweep_mesh_maya', tooltip=self._tooltips['create_sweep_mesh'], icon_size_override=20,
			padding_override=(7, 4, 4, 4), transparent_background=True, aligment='center', parent=self)
		self._create_type_button = qt.left_aligned_button(
			'', icon=':polyType', tooltip=self._tooltips['create_type'], icon_size_override=24,
			transparent_background=True, aligment='center', parent=self)
		self._dots_menu_button = qt.left_aligned_button(
			'', icon='menu_dots', tooltip='Left-click for more create primitive options', icon_size_override=20,
			padding_override=(7, 4 ,4, 4), transparent_background=True, aligment='center', parent=self)

	def _setup_layouts(self):
		"""
		Internal function that setup view layouts.
		"""

		self._main_layout = qt.vertical_layout(
			margins=(
				qt.consts.WINDOW_SIDE_PADDING, qt.consts.WINDOW_TOP_PADDING, qt.consts.WINDOW_SIDE_PADDING,
				qt.consts.WINDOW_BOTTOM_PADDING),
			spacing=qt.consts.DEFAULT_SPACING)
		self.setLayout(self._main_layout)

		self._primitives_layout = qt.horizontal_layout(spacing=qt.consts.SPACING)
		self._objects_layout = qt.grid_layout(
			spacing=qt.consts.SPACING,
			margins=(qt.consts.DEFAULT_SPACING, qt.consts.SMALL_SPACING, qt.consts.DEFAULT_SPACING, 0))
		self._objects_collapsable.add_layout(self._primitives_layout)
		self._objects_collapsable.add_layout(self._objects_layout)
		self._objects_collapsable_layout = qt.vertical_layout(margins=(0, 0, 0, 0))
		self._objects_collapsable_layout.addWidget(self._objects_collapsable)

		self._primitives_layout.addWidget(self._sphere_button)
		self._primitives_layout.addWidget(self._cube_button)
		self._primitives_layout.addWidget(self._cylinder_button)
		self._primitives_layout.addWidget(self._plane_button)
		self._primitives_layout.addWidget(self._torus_button)
		self._primitives_layout.addWidget(self._cone_button)
		self._primitives_layout.addWidget(self._create_polygon_button)
		self._primitives_layout.addWidget(self._create_sweep_mesh_button)
		self._primitives_layout.addWidget(self._create_type_button)
		self._primitives_layout.addWidget(self._dots_menu_button)

		self._main_layout.addLayout(self._objects_collapsable_layout)

	def _setup_signals(self):
		"""
		Internal function that setup signal connections.
		"""

		self._sphere_button.clicked.connect(self._controller.create_polygon_sphere)
		self._cube_button.clicked.connect(self._controller.create_polygon_cube)
		self._cylinder_button.clicked.connect(self._controller.create_polygon_cylinder)
		self._plane_button.clicked.connect(self._controller.create_polygon_plane)
		self._torus_button.clicked.connect(self._controller.create_polygon_torus)
		self._cone_button.clicked.connect(self._controller.create_polygon_cone)
		self._create_polygon_button.clicked.connect(self._controller.create_polygon_faces)
		self._create_sweep_mesh_button.clicked.connect(self._controller.create_sweep_mesh)
		self._create_type_button.clicked.connect(self._controller.create_polygon_type)
		self._dots_menu_button.create_menu_item(
			text='Create Disk', icon=':polyDisc', connection=self._controller.create_polygon_disk,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Pyramid', icon=':polyPyramid', connection=self._controller.create_polygon_pyramid,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Pipe', icon=':polyPipe', connection=self._controller.create_polygon_pipe,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Prism', icon=':polyPrism', connection=self._controller.create_polygon_prism,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Helix', icon=':polyHelix', connection=self._controller.create_polygon_helix,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Gear', icon=':polyGear', connection=self._controller.create_polygon_gear,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Soccer Ball', icon=':polySoccerBall', connection=self._controller.create_polygon_soccer_ball,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Platonic Solid', icon=':polySoccerBall',
			connection=self._controller.create_polygon_platonic_solid, mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create SVG', icon=':polySVG', connection=self._controller.create_polygon_svg,
			mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Super Ellipse', icon=':polySuperEllipse',
			connection=self._controller.create_polygon_super_ellipse, mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Spherical Harmonics', icon=':polySphericalHarmonics',
			connection=self._controller.create_polygon_spherical_harmonics, mouse_button=qt.Qt.LeftButton)
		self._dots_menu_button.create_menu_item(
			text='Create Ultra Shape', icon=':polyUltraShape',
			connection=self._controller.create_polygon_ultra_shape, mouse_button=qt.Qt.LeftButton)
