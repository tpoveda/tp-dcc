import math

import maya.mel as mel
import maya.cmds as cmds

from tp.core import log

logger = log.tpLogger


def playback_slider_object_path():
	"""
	Returns Python object that wraps Playback Slider Maya UI

	:return: Maya Playback slider path.
	:rtype: str
	"""

	return mel.eval('$tmpVar=$gPlayBackSlider')


def force_reset_current_frame():
	"""
	Forces the set of the current frame to itself to force a scene update.
	"""

	# turn off cycle check here prevents warnings of a meaningless cycles.
	cycle_check = cmds.cycleCheck(q=True, e=True)
	cmds.cycleCheck(e=False)
	try:
		cmds.currentTime(cmds.currentTime())
	finally:
		cmds.cycleCheck(e=cycle_check)


def set_current_frame(frame):
	"""
	Sets the current active frame.

	:param int frame: frame to set as active.
	"""

	cmds.currentTime(frame, edit=True)


def active_frame_range():
	"""
	Returns current frame range.

	:return: tuple with the start frame in the first index (0) and end frame in the second index (1)
	:rtype: tuple(int, int)
	"""

	return cmds.playbackOptions(query=True, minTime=True), cmds.playbackOptions(query=True, maxTime=True)


def set_active_frame_range(start_frame, end_frame):
	"""
	Sets current frame range.

	:param int start_frame: start frame.
	:param int end_frame: end frame.
	"""

	return cmds.playbackOptions(
		animationStartTime=start_frame, minTime=start_frame, animationEndTime=end_frame, maxTime=end_frame)


def active_animation_range():
	"""
	Returns current active animation range.

	:return: tuple with the start animation frame in the first index (0) and end animation frame in the second index (1)
	:rtype: tuple(int, int)
	:return:
	"""

	return cmds.playbackOptions(
		query=True, animationStartTime=True), cmds.playbackOptions(query=True, animationEndTime=True)


def set_active_animation_range(start_frame, end_frame):
	"""
	Sets current active animation frame range.

	:param int start_frame: start frame.
	:param int end_frame: end frame.
	"""

	return cmds.playbackOptions(animationStartTime=start_frame, animationEndTime=end_frame)


def start_frame():
	"""
	Returns current start frame.
	:return: start frame.
	:rtype: int
	"""

	return active_frame_range()[0]


def set_start_frame(frame):
	"""
	Sets current start frame.
	:param int frame: start frame.
	"""

	return set_active_frame_range(frame, end_frame())


def end_frame():
	"""
	Returns current end frame
	:return: end frame.
	:rtype: int
	"""

	return active_frame_range()[1]


def set_end_frame(frame):
	"""
	Sets current end frame.
	:param int frame: end frame.
	"""

	return set_active_frame_range(start_frame(), frame)


def visible_start_time():
	"""
	Get the first visible frame of the timeline.

	:return: The first frame of the visible timeline.
	:rtype int:
	"""

	return cmds.playbackOptions(q=1, min=1)


def visible_end_time():
	"""
	Get the last visible frame of the timeline.

	:return: The last frame of the visible timeline.
	:rtype int:
	"""

	return cmds.playbackOptions(q=1, max=1)


def visible_range():
	"""
	Get the start and end frame of the visible timeline.

	:return: The start and end frame of the visible timeline.
	:rtype int, int:
	"""

	return visible_start_time(), visible_end_time()


def scene_first_keyframe():
	"""
	returns time of first keyframe in the entire scene. Does not rely on animation time range.

	:return: frame of first keyframe
	:rtype int:
	"""

	curves = cmds.ls(type='animCurve')
	if curves:
		keys = cmds.keyframe(curves, q=True)
		if not keys:
			'No keys found in scene'
			return None
		return min(keys)
	return None


def scene_start_time():
	"""
	Get the first frame of the scene timeline.

	:return: The first frame of the scene timeline.
	:rtype int:
	"""

	return cmds.playbackOptions(q=1, ast=1)


def scene_end_time():
	"""
	Get the last frame of the scene timeline.

	:return: The last frame of the scene timeline.
	:rtype int:
	"""

	return cmds.playbackOptions(q=1, aet=1)


def scene_range():
	"""
	Get the start and end frame of the scene timeline.

	:return:  The start and end frame of the scene timeline.
	:rtype int, int:
	"""

	return scene_start_time(), scene_end_time()


def scene_last_keyframe():
	"""
	returns time of last keyframe in the entire scene. Does not rely on animation time range.

	:return: frame of last keyframe
	:rtype int:
	"""

	curves = cmds.ls(type='animCurve')
	if curves:
		keys = cmds.keyframe(curves, q=True)
		if not keys:
			'No keys found in scene'
			return None
		return max(keys)
	return None


def first_and_last_selected_frames():
	"""
	Returns the first and last selected frames.

	:return: list containing the first and last selected frames.
	:rtype: list(int, int)
	"""

	total_frames = cmds.keyframe(query=True, selected=True)
	total_frames.sort()
	if not total_frames:
		logger.warning('No frames interval selected')
		return [0, 0]

	return [total_frames[0], total_frames[-1]]


def selected_range_from_timeline():
	"""
	Returns a selection on the timeline else None if there is no selection.

	:return: The start and end frame of the timeline selection.
	:rtype int, int:
	"""

	try:
		gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')  # vollects timeslider
		if cmds.timeControl(gPlayBackSlider, q=True, rv=True):  # is a selection visible
			min_frame, max_frame = cmds.timeControl(gPlayBackSlider, q=True, ra=True)  # collect frame array.
		else:
			return None, None
	except Exception as exc:
		# failed to find the playback slider.
		return None, None

	return min_frame, max_frame


def selected_range(time_control=None):
	"""
	Returns the current selected frame range.

	:param str time_control: time control object path to use. If not given, standard Maya time range object will be
		used.
	:return: selected frame range.
	:rtype: list[int, int]
	"""

	time_control = time_control or playback_slider_object_path()
	selected_frame_range = cmds.timeControl(time_control, query=True, rangeArray=True)

	selected_curves = cmds.keyframe(query=True, name=True, selected=True)
	first_curve = selected_curves[0] if selected_curves else None
	if selected_frame_range[1] - selected_frame_range[0] <= 1 and first_curve:
		selected_frame_range = first_and_last_selected_frames()
		selected_frame_range[1] = math.ceil(selected_frame_range[1] + 1)

	return selected_frame_range


def selected_or_current_frame_range(time_control=None):
	"""
	Returns the current selected frame range or the current frame range if frame range is selected.

	:param str time_control: time control object path to use. If not given, standard Maya time range object will be
		used.
	:return: selected or current frame range.
	:rtype: list(int, int)
	"""

	frame_range = selected_range(time_control=time_control)
	start, end = frame_range
	#  when the user only has one frame and no frame selected
	if end - start == 1:
		frame_range = active_frame_range()

	return frame_range


def range_from_attribute_curves(attr_curve_list):
	"""
	From a list of attribute curves find the first and last keyframes.

	:param list[AttrCurve] attr_curve_list:
	:return:  The start and end frame of the passed curves.
	:rtype int, int:
	"""

	selected_keys = sorted(cmds.keyframe(attr_curve_list, q=True, sl=True))
	if selected_keys:
		return min(selected_keys), max(selected_keys)
	return None, None


def keyframe_range_from_nodes(node_list):
	"""
	Returns the keyframe range from a group of nodes. This will return None if there are no valid keyframes on the nodes.

	:param list node_list: List of maya nodes with keyframes.
	:return: The start and end frame of the keyframes of the passed list.
	:rtype int, int:
	"""

	if node_list:
		key_list = cmds.keyframe(node_list, q=True) if isinstance(node_list, list) else None
		if key_list:
			min_frame = min(key_list)
			max_frame = max(key_list)
			return min_frame, max_frame
		else:
			return None, None
	else:
		return None, None


def keyframe_range_from_scene():
	"""
	From all scene animation curves get the first and last keyframe.

	:return: The start and end frame of all animation in the scene.
	:rtype int, int:
	"""

	return scene_first_keyframe(), scene_last_keyframe()


def times(node_list=None, min_selected_frames=1, ignore_selection=True):
	"""
	Returns the frame range in cascading order of importance.

	#1 Selected Timeline
	#2 (Optional) Curve Editor Selection
	#3 (Optional) Node list
	#4 Animation curves in scene
	#5 Greatest of zoomed timeline or scene timeline

	:param list[PyNode] node_list: List of objects we should use to derive time range.
	:param int min_selected_frames: Minimum number of required selected frames.
	:param bool ignore_selection: This ignores the logic for deriving keyframe range from a selection of attribute curves.
	:return: The best choice of first and last frame values.
	:rtype int, int:
	"""

	frame_range = selected_range_from_timeline()  # 1 selected timeline
	log_str = '#1 Using user selected timeline.'

	if not any(x is None for x in frame_range):
		selected_frames = frame_range[-1] - frame_range[0]
	else:
		selected_frames = 0

	if any(x is None for x in frame_range) or selected_frames < min_selected_frames:
		# check returned frame range, if the range is less than the expected min. Cascade.
		if not ignore_selection:
			# 2 curve editor
			attr_curves = cmds.keyframe(q=True, selected=True, name=True)
			if attr_curves:
				frame_range = range_from_attribute_curves(attr_curves)
				log_str = '#2.1 Using user selected attr curves.'

		if any(x is None for x in frame_range) and node_list:
			# 3 passed objects with keys
			frame_range = keyframe_range_from_nodes(node_list)
			log_str = '#2.2 Using passed objects.'

		if any(x is None for x in frame_range):
			# 4 if we didn't get anything from our passed objects, see if we have any animation in the scene.
			frame_range = keyframe_range_from_scene()
			log_str = '#3 Using scene animation curves'

		if any(x is None for x in frame_range):
			# 5 if we didn't get a valid selection use the greatest of scene or visible timeline.
			frame_range = min(scene_start_time(), visible_start_time()), max(scene_end_time(), visible_end_time())
			log_str = '#3 Using scene zoomed timeline.'

	logger.debug(log_str)

	return frame_range


def play_frame_range_forward(start_frame=None, end_frame=None):
	"""
	Plays timeline and sets given start and end frames if necessary.

	:param int or None start_frame: optional start frame.
	:param int or None end_frame: optional end frame.
	"""

	if start_frame is not None:
		set_start_frame(start_frame)
	if end_frame is not None:
		set_end_frame(end_frame)

	cmds.play(forward=True)
