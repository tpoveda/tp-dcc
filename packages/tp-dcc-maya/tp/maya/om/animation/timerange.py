import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim


FRAME_TO_UNIT = {
	25: OpenMaya.MTime.k25FPS,
	30: OpenMaya.MTime.k30FPS,
	48: OpenMaya.MTime.k48FPS,
	2: OpenMaya.MTime.k2FPS,
	3: OpenMaya.MTime.k3FPS,
	4: OpenMaya.MTime.k4FPS,
	5: OpenMaya.MTime.k5FPS,
	6: OpenMaya.MTime.k6FPS,
	8: OpenMaya.MTime.k8FPS,
	10: OpenMaya.MTime.k10FPS,
	12: OpenMaya.MTime.k12FPS,
	15: OpenMaya.MTime.k15FPS,
	16: OpenMaya.MTime.k16FPS,
	20: OpenMaya.MTime.k20FPS,
	23.976: OpenMaya.MTime.k23_976FPS,
	24: OpenMaya.MTime.k24FPS,
	29.9: OpenMaya.MTime.k29_97DF,
	29.97: OpenMaya.MTime.k29_97FPS,
	40: OpenMaya.MTime.k40FPS,
	47.952: OpenMaya.MTime.k47_952FPS,
	50: OpenMaya.MTime.k50FPS,
	59.94: OpenMaya.MTime.k59_94FPS,
	60: OpenMaya.MTime.k60FPS,
	75: OpenMaya.MTime.k75FPS,
	80: OpenMaya.MTime.k80FPS,
	100: OpenMaya.MTime.k100FPS,
	120: OpenMaya.MTime.k120FPS,
	125: OpenMaya.MTime.k125FPS,
	150: OpenMaya.MTime.k150FPS,
	200: OpenMaya.MTime.k200FPS,
	240: OpenMaya.MTime.k240FPS,
	250: OpenMaya.MTime.k250FPS,
	300: OpenMaya.MTime.k300FPS,
	375: OpenMaya.MTime.k375FPS,
	400: OpenMaya.MTime.k400FPS,
	500: OpenMaya.MTime.k500FPS,
	600: OpenMaya.MTime.k600FPS,
	750: OpenMaya.MTime.k750FPS,
	1200: OpenMaya.MTime.k1200FPS,
	1500: OpenMaya.MTime.k1500FPS,
	2000: OpenMaya.MTime.k2000FPS,
	3000: OpenMaya.MTime.k3000FPS,
	6000: OpenMaya.MTime.k6000FPS,
	44100: OpenMaya.MTime.k44100FPS,
	48000: OpenMaya.MTime.k48000FPS
}

UNIT_TO_FRAME = {
	OpenMaya.MTime.k25FPS: 25,
	OpenMaya.MTime.k30FPS: 30,
	OpenMaya.MTime.k48FPS: 48,
	OpenMaya.MTime.k2FPS: 2,
	OpenMaya.MTime.k3FPS: 3,
	OpenMaya.MTime.k4FPS: 4,
	OpenMaya.MTime.k5FPS: 5,
	OpenMaya.MTime.k6FPS: 6,
	OpenMaya.MTime.k8FPS: 8,
	OpenMaya.MTime.k10FPS: 10,
	OpenMaya.MTime.k12FPS: 12,
	OpenMaya.MTime.k15FPS: 15,
	OpenMaya.MTime.k16FPS: 16,
	OpenMaya.MTime.k20FPS: 20,
	OpenMaya.MTime.k23_976FPS: 23.976,
	OpenMaya.MTime.k24FPS: 24,
	OpenMaya.MTime.k29_97DF: 29.9,
	OpenMaya.MTime.k29_97FPS: 29.97,
	OpenMaya.MTime.k40FPS: 40,
	OpenMaya.MTime.k47_952FPS: 47.952,
	OpenMaya.MTime.k50FPS: 50,
	OpenMaya.MTime.k59_94FPS: 59.94,
	OpenMaya.MTime.k60FPS: 60,
	OpenMaya.MTime.k75FPS: 75,
	OpenMaya.MTime.k80FPS: 80,
	OpenMaya.MTime.k100FPS: 100,
	OpenMaya.MTime.k120FPS: 120,
	OpenMaya.MTime.k125FPS: 125,
	OpenMaya.MTime.k150FPS: 150,
	OpenMaya.MTime.k200FPS: 200,
	OpenMaya.MTime.k240FPS: 240,
	OpenMaya.MTime.k250FPS: 250,
	OpenMaya.MTime.k300FPS: 300,
	OpenMaya.MTime.k375FPS: 375,
	OpenMaya.MTime.k400FPS: 400,
	OpenMaya.MTime.k500FPS: 500,
	OpenMaya.MTime.k600FPS: 600,
	OpenMaya.MTime.k750FPS: 750,
	OpenMaya.MTime.k1200FPS: 1200,
	OpenMaya.MTime.k1500FPS: 1500,
	OpenMaya.MTime.k2000FPS: 2000,
	OpenMaya.MTime.k3000FPS: 3000,
	OpenMaya.MTime.k6000FPS: 6000,
	OpenMaya.MTime.k44100FPS: 44100,
	OpenMaya.MTime.k48000FPS: 48000
}


def current_time_info():
	"""
	Returns a dictionary with all the current timeline settings.

	:return: time info data.
	:rtype: dict
	"""

	current = OpenMayaAnim.MAnimControl.currentTime()
	return {
		'currentTime': current,
		'start': OpenMayaAnim.MAnimControl.minTime(),
		'end': OpenMayaAnim.MAnimControl.maxTime(),
		'unit': current.uiUnit(),
		'fps': UNIT_TO_FRAME[current.uiUnit()]
	}


def iterate_frame_range_dg_context(start, end, step=1):
	"""
	Generator function that iterates over a frame range returning a MDGContext for the current frame.

	:param int start: the start frame.
	:param int end: the end frame.
	:param int step: amount of frames to skip between frames.
	:return: generator function with each element being a MDGContext with the current frame applied.
	:rtype: collections.Iterator[:class:`OpenMaya.MDGContext`
	"""

	current_time = OpenMayaAnim.MAnimControl.currentTime()
	per_frame = OpenMaya.MTime(start, current_time.unit)
	for frame in range(start, end + 1, step):
		context = OpenMaya.MDGContext(per_frame)
		yield context
		per_frame += 1


def iterate_frames_dg_context(frames, step=1):
	"""
	Generator function that iterates over a time range returning a MDGContext instance for the current frame.

	:param list(int or float) frames: list of frame numbers to iterate.
	:param int step: amount of frame sto skip between frames.
	:return: generator function with each element being a MDGContext with the current frame applied.
	:rtype: generator(OpenMaya.MDGContext)
	"""

	current_time = OpenMayaAnim.MAnimControl.currentTime()
	for i in range(0, len(frames), step):
		frame_time = OpenMaya.MTime(frames[i], current_time.unit)
		context = OpenMaya.MDGContext(frame_time)
		yield context

