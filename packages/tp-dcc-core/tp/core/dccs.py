from tp.core import consts
from tp.common.python import osplatform

DEFAULT_DCC_PORT = 65500


Standalone = 'standalone'
Maya = 'maya'
Max = '3dsmax'
MotionBuilder = 'mobu'
Houdini = 'houdini'
Nuke = 'nuke'
Unreal = 'unreal'
Blender = 'blender'
SubstancePainter = 'painter'
SubstanceDesigner = 'designer'
Fusion = 'fusion'

ALL = [
	Maya, Max, MotionBuilder, Houdini, Nuke, Unreal, Blender, SubstancePainter, SubstanceDesigner, Fusion
]

NiceNames = dict([
	(Maya, 'Maya'),
	(Max, '3ds Max'),
	(MotionBuilder, 'MotionBuilder'),
	(Houdini, 'Houdini'),
	(Nuke, 'Nuke'),
	(Unreal, 'Unreal'),
	(Blender, 'Blender'),
	(SubstancePainter, 'SubstancePainter'),
	(SubstanceDesigner, 'SubstanceDesigner'),
	(Fusion, 'Fusion')
])

Packages = dict([
	('maya', Maya),
	('pymxs', Max),
	('MaxPlus', Max),
	('pyfbsdk', MotionBuilder),
	('hou', Houdini),
	('nuke', Nuke),
	('unreal', Unreal),
	('bpy', Blender),
	('substance_painter', SubstancePainter),
	('sd', SubstanceDesigner),
	('fusionscript', Fusion),
	('PeyeonScript', Fusion)
])

# TODO: Add support for both MacOS and Linux
Executables = {
	Maya: {osplatform.Platforms.Windows: 'maya.exe'},
	Max: {osplatform.Platforms.Windows: '3dsmax.exe'},
	MotionBuilder: {osplatform.Platforms.Windows: 'motionbuilder.exe'},
	Houdini: {osplatform.Platforms.Windows: 'houdini'},
	Nuke: {osplatform.Platforms.Windows: 'Nuke'},
	Unreal: {osplatform.Platforms.Windows: 'UnrealEditor.exe'},
	Blender: {osplatform.Platforms.Windows: 'blender.exe'},
	SubstancePainter: {osplatform.Platforms.Windows: 'painter.exe'},
	SubstanceDesigner: {osplatform.Platforms.Windows: 'designer.exe'},
	Fusion: {osplatform.Platforms.Windows: 'Fusion.exe'}
}

Ports = {
	'Undefined': DEFAULT_DCC_PORT,              # 65500
	Standalone: DEFAULT_DCC_PORT + 1,           # 65501
	Maya: DEFAULT_DCC_PORT + 2,                 # 65502
	Max: DEFAULT_DCC_PORT + 3,                  # 65503
	MotionBuilder: DEFAULT_DCC_PORT + 4,        # 65504
	Houdini: DEFAULT_DCC_PORT + 5,              # 65505
	Nuke: DEFAULT_DCC_PORT + 6,                 # 65506
	Blender: DEFAULT_DCC_PORT + 7,              # 65507
	SubstancePainter: DEFAULT_DCC_PORT + 8,     # 65508
	SubstanceDesigner: DEFAULT_DCC_PORT + 9,    # 65509
	Fusion: DEFAULT_DCC_PORT + 10,              # 65510
	Unreal: 30010                              # Default Unreal Remote Server Plugin port
}


class Callbacks:
	Shutdown = (consts.CallbackTypes.Shutdown, {'type': 'simple'})
	Tick = (consts.CallbackTypes.Tick, {'type': 'simple'})
	ScenePreCreated = (consts.CallbackTypes.ScenePreCreated, {'type': 'simple'})
	ScenePostCreated = (consts.CallbackTypes.ScenePostCreated, {'type': 'simple'})
	SceneNewRequested = (consts.CallbackTypes.SceneNewRequested, {'type': 'simple'})
	SceneNewFinished = (consts.CallbackTypes.SceneNewFinished, {'type': 'simple'})
	SceneSaveRequested = (consts.CallbackTypes.SceneSaveRequested, {'type': 'simple'})
	SceneSaveFinished = (consts.CallbackTypes.SceneSaveFinished, {'type': 'simple'})
	SceneOpenRequested = (consts.CallbackTypes.SceneOpenRequested, {'type': 'simple'})
	SceneOpenFinished = (consts.CallbackTypes.SceneOpenFinished, {'type': 'simple'})
	UserPropertyPreChanged = (consts.CallbackTypes.UserPropertyPreChanged, {'type': 'filter'})
	UserPropertyPostChanged = (consts.CallbackTypes.UserPropertyPostChanged, {'type': 'filter'})
	NodeSelect = (consts.CallbackTypes.NodeSelect, {'type': 'filter'})
	NodeAdded = (consts.CallbackTypes.NodeAdded, {'type': 'filter'})
	NodeDeleted = (consts.CallbackTypes.NodeDeleted, {'type': 'filter'})
	ReferencePreLoaded = (consts.CallbackTypes.ReferencePreLoaded, {'type': 'simple'})
	ReferencePostLoaded = (consts.CallbackTypes.ReferencePostLoaded, {'type': 'simple'})
