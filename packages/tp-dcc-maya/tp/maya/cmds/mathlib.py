from __future__ import annotations

from typing import Iterable, List

import maya.cmds as cmds


def vector_from_two_points(
		point_a: Iterable[float, float, float] | str | None = None,
		point_b: Iterable[float, float, float] | str | None = None) -> List[float, float, float]:
	"""
	Returns the list representing the vector from point A to point B.

	:param Iterable[float, float, float] or str or None point_a: point A to get vector for.
	:param Iterable[float, float, float] or str or None point_b: point B to get vector for.
	:return: vector list.
	:rtype: List[float, float, float]
	"""

	def _get_world_position(_pos):
		if isinstance(_pos, list) or isinstance(_pos, tuple) and len(_pos) == 3:
			return _pos
		elif isinstance(_pos, str):
			return cmds.xform(_pos, query=True, worldSpace=True, translation=True)
		raise RuntimeError('Must provide cartesian position or transform node name')

	return [b - a for a, b in zip(_get_world_position(point_a), _get_world_position(point_b))]


def distance_between_points(
		point_a: Iterable[float, float, float] | str | None = None,
		point_b: Iterable[float, float, float] | str | None = None) -> float:
	"""
	Returns the total distance between two given points.

	:param Iterable[float, float, float] or str or None point_a: point A to get vector for.
	:param Iterable[float, float, float] or str or None point_b: point B to get vector for.
	:return: vector distance.
	:rtype: float
	"""

	vector_ab = vector_from_two_points(point_a, point_b)
	return pow(sum([pow(n, 2) for n in vector_ab]), 0.5)
