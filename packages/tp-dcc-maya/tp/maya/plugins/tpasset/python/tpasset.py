from __future__ import annotations

from overrides import override

import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaUI as OpenMayaUI
import maya.api.OpenMayaRender as OpenMayaRender

from tp.maya.api import asset


maya_useNewAPI = True


class AssetNode(OpenMayaUI.MPxLocatorNode):

	TYPE_NAME = asset.AssetWrapper.ASSET_TYPE_NAME
	TYPE_ID = OpenMaya.MTypeId(0x0005E5EF)
	DRAW_CLASSIFICATION = f'drawdb/geometry/{TYPE_NAME}'
	DRAW_REGISTRANT_ID = 'TpAssetNode'

	STATIC_MESH_COLOR = OpenMaya.MColor((0.7450, 0.6274, 0.3921))
	SKELETAL_MESH_COLOR = OpenMaya.MColor((0.3607, 0.7333, 0.7490))
	SELECTED_COLOR = OpenMaya.MColor((0.7294, 0.5137, 0.8117))

	ASSET_TYPE = OpenMaya.MObject()
	SHOW_UI = OpenMaya.MObject()
	UI_SCALE = OpenMaya.MObject()
	EXPORT = OpenMaya.MObject()
	IS_NANITE = OpenMaya.MObject()
	IS_SKELETAL = OpenMaya.MObject()
	UNREAL_SKELETON = OpenMaya.MObject()
	UNREAL_PHYSICS_ASSET = OpenMaya.MObject()

	@classmethod
	def creator(cls):
		return cls()

	@classmethod
	def initialize(cls):
		numeric_attr = OpenMaya.MFnNumericAttribute()
		message_attr = OpenMaya.MFnMessageAttribute()
		typed_attr = OpenMaya.MFnTypedAttribute()
		enum_attr = OpenMaya.MFnEnumAttribute()

		cls.ASSET_TYPE = enum_attr.create(asset.AssetWrapper.PLUG_ASSET_TYPE, 'at', 0)
		enum_attr.keyable = True
		assets = [(i, asset_type) for i, asset_type in enumerate(asset.ASSET_TYPES)]
		for found_asset in assets:
			enum_attr.addField(found_asset[1], found_asset[0])

		cls.SHOW_UI = numeric_attr.create(asset.AssetWrapper.PLUG_SHOW_UI, 'si', OpenMaya.MFnNumericData.kBoolean, True)
		numeric_attr.keyable = True
		numeric_attr.setMin(0)
		numeric_attr.setMax(1)

		cls.UI_SCALE = numeric_attr.create(asset.AssetWrapper.PLUG_UI_SCALE, 'uis', OpenMaya.MFnNumericData.kFloat, 1.0)
		numeric_attr.keyable = True
		numeric_attr.setMin(0.1)
		numeric_attr.setMax(10.0)

		cls.EXPORT = numeric_attr.create(asset.AssetWrapper.PLUG_EXPORT, 'e', OpenMaya.MFnNumericData.kBoolean, True)
		numeric_attr.keyable = True
		numeric_attr.setMin(0)
		numeric_attr.setMax(1)

		cls.IS_NANITE = numeric_attr.create(asset.AssetWrapper.PLUG_IS_NANITE, 'nn', OpenMaya.MFnNumericData.kBoolean, True)
		numeric_attr.keyable = True
		numeric_attr.setMin(0)
		numeric_attr.setMax(1)

		cls.IS_SKELETAL = numeric_attr.create(asset.AssetWrapper.PLUG_IS_SKELETAL, 'sk', OpenMaya.MFnNumericData.kBoolean, False)
		numeric_attr.keyable = True
		numeric_attr.setMin(0)
		numeric_attr.setMax(1)

		cls.UNREAL_SKELETON = typed_attr.create(asset.AssetWrapper.PLUG_UNREAL_SKELETON, 'usk', OpenMaya.MFnData.kString)
		typed_attr.keyable = True

		cls.UNREAL_PHYSICS_ASSET = typed_attr.create(asset.AssetWrapper.PLUG_UNREAL_PHYSICS, 'uph', OpenMaya.MFnData.kString)
		typed_attr.keyable = True

		cls.addAttribute(cls.ASSET_TYPE)
		cls.addAttribute(cls.SHOW_UI)
		cls.addAttribute(cls.UI_SCALE)
		cls.addAttribute(cls.EXPORT)
		cls.addAttribute(cls.IS_NANITE)
		cls.addAttribute(cls.IS_SKELETAL)
		cls.addAttribute(cls.UNREAL_SKELETON)
		cls.addAttribute(cls.UNREAL_PHYSICS_ASSET)

	@override(check_signature=False)
	def isBounded(self):
		return True

	@override(check_signature=False)
	def boundingBox(self):
		size = 100.0
		ui_scale = OpenMaya.MFnDependencyNode(self.thisMObject()).findPlug(asset.AssetWrapper.PLUG_UI_SCALE, False).asFloat()
		size *= ui_scale
		return OpenMaya.MBoundingBox(OpenMaya.MPoint(-size, -size, -size), OpenMaya.MPoint(size, size, size))


class AssetUserData(OpenMaya.MUserData):
	def __init__(self, delete_after_use=False):
		super().__init__(delete_after_use)

		self.show_ui = False
		self.ui_scale = 1.0
		self.is_skeletal = 0
		self.wireframe_color = AssetNode.STATIC_MESH_COLOR


class AssetDrawOverride(OpenMayaRender.MPxDrawOverride):

	NAME = 'tpAssetDrawOverride'

	@classmethod
	def creator(cls, mobj: OpenMaya.MObject):
		return cls(mobj)

	def __init__(self, mobj: OpenMaya.MObject):
		super().__init__(mobj, None, True)

	@override(check_signature=False)
	def supportedDrawAPIs(self):
		return OpenMayaRender.MRenderer.kAllDevices

	@override(check_signature=False)
	def hasUIDrawables(self):
		return True

	@override(check_signature=False)
	def prepareForDraw(
			self, mobj_path: OpenMaya.MDagPath, camera_path: OpenMaya.MDagPath,
			frame_context: OpenMayaRender.MFrameContext, old_data: AssetUserData | None):
		data = old_data
		if not data:
			data = AssetUserData()

		locator_obj = mobj_path.node()
		node_fn = OpenMaya.MFnDependencyNode(locator_obj)
		data.show_ui = node_fn.findPlug(asset.AssetWrapper.PLUG_SHOW_UI, False).asBool()
		data.ui_scale = node_fn.findPlug(asset.AssetWrapper.PLUG_UI_SCALE, False).asFloat()
		data.is_skeletal = node_fn.findPlug(asset.AssetWrapper.PLUG_IS_SKELETAL, False).asBool()

		display_status = OpenMayaRender.MGeometryUtilities.displayStatus(mobj_path)
		if display_status == OpenMayaRender.MGeometryUtilities.kDormant:
			if data.is_skeletal:
				data.wireframe_color = AssetNode.SKELETAL_MESH_COLOR
			else:
				data.wireframe_color = AssetNode.STATIC_MESH_COLOR
		else:
			data.wireframe_color = AssetNode.SELECTED_COLOR

		return data

	@override(check_signature=False)
	def addUIDrawables(
			self, obj_path: OpenMaya.MDagPath, draw_manager: OpenMayaRender.MUIDrawManager,
			frame_context: OpenMayaRender.MFrameContext, data: AssetUserData):

		draw_manager.beginDrawable()

		scale = data.ui_scale
		draw_manager.setColor(data.wireframe_color)
		draw_manager.setLineWidth(2)

		# Circle
		draw_manager.circle(OpenMaya.MPoint(0, 0, 0), OpenMaya.MVector(0, 1 * scale, 0), 100 * scale, False)

		# T
		draw_manager.line(OpenMaya.MPoint(0, 0, -60 * scale), OpenMaya.MPoint(0, 0, 100 * scale))
		draw_manager.line(OpenMaya.MPoint(-80 * scale, 0, -60 * scale), OpenMaya.MPoint(80 * scale, 0, -60 * scale))

		draw_manager.endDrawable()


def initializePlugin(mobj: OpenMaya.MObject):
	mplugin = OpenMaya.MFnPlugin(mobj, 'Tomas Poveda', '1.0', 'Any')
	try:
		mplugin.registerNode(
			AssetNode.TYPE_NAME, AssetNode.TYPE_ID, AssetNode.creator, AssetNode.initialize,
			OpenMaya.MPxNode.kLocatorNode, AssetNode.DRAW_CLASSIFICATION)
	except Exception as err:
		OpenMaya.MGlobal.displayError(err)
		OpenMaya.MGlobal.displayError(f'Failed to register node: "{AssetNode.TYPE_NAME}"')

	try:
		OpenMayaRender.MDrawRegistry.registerDrawOverrideCreator(
			AssetNode.DRAW_CLASSIFICATION, AssetNode.DRAW_REGISTRANT_ID, AssetDrawOverride.creator)
	except Exception as err:
		OpenMaya.MGlobal.displayError(err)
		OpenMaya.MGlobal.displayError(f'Failed to register draw override: "{AssetNode.TYPE_NAME}"')


def uninitializePlugin(mobj: OpenMaya.MObject):
	mplugin = OpenMaya.MFnPlugin(mobj)

	try:
		OpenMayaRender.MDrawRegistry.deregisterDrawOverrideCreator(
			AssetNode.DRAW_CLASSIFICATION, AssetNode.DRAW_REGISTRANT_ID)
	except Exception as err:
		OpenMaya.MGlobal.displayError(err)
		OpenMaya.MGlobal.displayError(f'Failed to deregister draw override: "{AssetNode.TYPE_NAME}"')

	try:
		mplugin.deregisterNode(AssetNode.TYPE_ID)
	except Exception as err:
		OpenMaya.MGlobal.displayError(err)
		OpenMaya.MGlobal.displayError(f'Failed to deregister node: "{AssetNode.TYPE_NAME}"')
