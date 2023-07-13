import maya.cmds as cmds
import maya.mel as mel

from tp.core import log
from tp.maya.cmds.nodes import matching

logger = log.modelLogger


def create_primitive_and_match(primitive: str = 'cube') -> str:
	"""
	Creates a primitive object og the given type and matches it to the currently selected object within scene.
	Supported primitive types:
		"cube", "sphere", "cylinder", "plane", "nurbsCircle", "torus", "cone", "pyramid", "pipe", "helix", "gear",
		"soccerball", "svg", "superEllipsoid", "sphericalHarmonics", "ultraShape", "disk", "platonicSolid"

	:param str primitive: name of the primitive to create.
	:return: name of the newly created object.
	:rtype: str
	"""

	selected_node_names = cmds.ls(selection=True, long=True)
	if primitive == 'cube':
		new_primitive = cmds.polyCube()[0]
	elif primitive == 'sphere':
		new_primitive = cmds.polySphere(subdivisionsAxis=12, subdivisionsHeight=8)[0]
	elif primitive == 'cylinder':
		new_primitive = cmds.polyCylinder(subdivisionsAxis=12)[0]
	elif primitive == 'plane':
		new_primitive = cmds.polyPlane(subdivisionsHeight=1, subdivisionsWidth=1)[0]
	elif primitive == 'nurbsCircle':
		new_primitive = cmds.circle(normal=[0, 1, 0])[0]
	elif primitive == 'torus':
		new_primitive = cmds.polyTorus()[0]
	elif primitive == 'cone':
		new_primitive = cmds.polyCone()[0]
	elif primitive == 'disk':
		new_primitive = mel.eval('polyDisc;')[0]
	elif primitive == 'pyramid':
		new_primitive = cmds.polyPyramid()[0]
	elif primitive == 'pipe':
		new_primitive = cmds.polyPipe()[0]
	elif primitive == 'prism':
		new_primitive = cmds.polyPrism()[0]
	elif primitive == 'helix':
		new_primitive = cmds.polyHelix()[0]
	elif primitive == 'gear':
		new_primitive = mel.eval('polyGear')[0]
	elif primitive == 'platonicSolid':
		new_primitive = mel.eval('polyPlatonic -primitive 4 -subdivisionMode 0 -subdivisions 0 -radius 1 -sphericalInflation 1;')[0]
	elif primitive == 'soccerBall':
		new_primitive = mel.eval('polyPrimitive -r 1 -l 0.4036 -ax 0 1 0 -pt 0  -cuv 4 -ch 1')[0]
	elif primitive == 'superEllipsoid':
		new_primitive = mel.eval('polySuperShape -radius 1 -shape "SuperEllipse" -horizontalDivisions 16 -verticalDivisions 16 -createUV 2 -mergeVertices 1 -horizontalRevolutions 1 -verticalRevolutions 1 -verticalOffset 0 -internalRadius 0 -xOffset 0 -zOffset 0 -ve 1 -he 1 -em 1 -vm1 0 -ve1 1 -vm2 0 -ve2 1 -hm1 0 -he1 1 -hm2 0 -he2 1 -u0 0 -u1 1 -u2 1 -u3 0.5 -u4 0 -u5 1 -u6 1 -u7 1 -u8 0 -u9 1 -u10 1 -u11 0.5 -u12 0 -u13 1 -u14 1 -u15 1 -um 0;')[0]
	elif primitive == 'sphericalHarmonics':
		new_primitive = mel.eval('polySuperShape -radius 1 -shape "SphericalHarmonics" -horizontalDivisions 16 -verticalDivisions 16 -createUV 2 -mergeVertices 1 -horizontalRevolutions 1 -verticalRevolutions 1 -verticalOffset 0 -internalRadius 0 -xOffset 0 -zOffset 0 -ve 1 -he 1 -em 1 -vm1 0 -ve1 1 -vm2 0 -ve2 1 -hm1 0 -he1 1 -hm2 0 -he2 1 -u0 0 -u1 1 -u2 1 -u3 0.5 -u4 0 -u5 1 -u6 1 -u7 1 -u8 0 -u9 1 -u10 1 -u11 0.5 -u12 0 -u13 1 -u14 1 -u15 1 -um 0;')[0]
	elif primitive == 'ultraShape':
		new_primitive = mel.eval('polySuperShape -radius 1 -shape "UltraShape" -horizontalDivisions 16 -verticalDivisions 16 -createUV 2 -mergeVertices 1 -horizontalRevolutions 1 -verticalRevolutions 1 -verticalOffset 0 -internalRadius 0 -xOffset 0 -zOffset 0 -ve 1 -he 1 -em 1 -vm1 0 -ve1 1 -vm2 0 -ve2 1 -hm1 0 -he1 1 -hm2 0 -he2 1 -u0 0 -u1 1 -u2 1 -u3 0.5 -u4 0 -u5 1 -u6 1 -u7 1 -u8 0 -u9 1 -u10 1 -u11 0.5 -u12 0 -u13 1 -u14 1 -u15 1 -um 0;')[0]
	else:
		logger.warning(f'Invalid object not supported: {primitive}')
		return ''

	if selected_node_names:
		matching.match_to_center_nodes_components(
			new_primitive, selected_node_names, set_object_mode=True, orient_to_components=True)
		logger.info(f'Created and matched "{new_primitive}"')
	else:
		logger.info(f'Created "{new_primitive}"')

	mel.eval('setToolTo ShowManips')

	return new_primitive
