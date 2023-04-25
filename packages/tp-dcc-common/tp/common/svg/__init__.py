#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality related with SVG operations
"""

from __future__ import print_function, division, absolute_import

import os
import re
import math
import logging
from xml.dom import minidom
from collections import OrderedDict

from Qt.QtCore import QPointF, QRectF
from Qt.QtGui import QPainterPath, QTransform, QPolygonF, QImage, QPainter
from Qt.QtSvg import QSvgRenderer


from pysvg import parser

_COMMANDS = set('MmZzLlHhVvCcSsQqTtAa')
_COMMAND_RE = re.compile('([MmZzLlHhVvCcSsQqTtAa])')
_FLOAT_RE = re.compile('[-+]?[0-9]*\\.?[0-9]+(?:[eE][-+]?[0-9]+)?')

LOGGER = logging.getLogger()


def generate_svg(svg_file):

	draw_set = list()
	bounding_rect = QRectF()

	for style, path, pathType, id in get_path_order_from_svg_file(svg_file):

		# We do not load the init rect item which indicates document settings
		if style.get('display') == 'none':
			continue
		if pathType == 'path':
			svgPath = create_svg_path(path)
		elif pathType in ('circle', 'ellipse'):
			svgPath = create_ellipse_path(path)
		elif pathType == 'rect':
			svgPath = create_rect_path(path)
		elif pathType == 'polygon':
			svgPath = create_polygon_path(path)
		else:
			continue
		bounding_rect = bounding_rect.united(svgPath.boundingRect())
		draw_set.append([style, svgPath])

	for bundle in draw_set:
		path = bundle.pop()
		offset = path.boundingRect().topLeft() - bounding_rect.topLeft()
		path.translate(path.boundingRect().topLeft() * -1)
		path.translate(offset)
		bundle.append(path)

	return (bounding_rect, draw_set)


def get_style_tag(doc):

	root = doc.documentElement
	for node in root.childNodes:
		if node.nodeType == node.ELEMENT_NODE and node.tagName == 'style':
			result = dict()
			for data in node.firstChild.data.strip().split():
				m = re.match('^\\.(.+)\\{(.+)\\}$', data)
				if m:
					result[m.group(1)] = dict([s.split(':') for s in m.group(2).split(':') if s])
			return ('styleElement', result)
	return ('styleAttribute', {})


def get_all_svg_tags(doc):
	def check_tag_name(root, listData=[]):
		if root.childNodes:
			for node in root.childNodes:
				if node.nodeType == node.ELEMENT_NODE:
					if node.tagName in ('path', 'circle', 'ellipse', 'rect', 'polygon'):
						listData.append(node)
					check_tag_name(node, listData)
	root = doc.documentElement
	svg_list = list()
	check_tag_name(root, svg_list)
	return svg_list


def decode_svg_path_string_replace(pathString):
	d = _tokenize_path_replace(pathString)
	path_order = list()
	pop_data = d.pop(0)
	while d:
		if pop_data and pop_data.isalpha():
			numeric_buffer = list()
			try:
				num = d.pop(0)
				while not num.isalpha():
					numeric_buffer.append(float(num))
					num = d.pop(0)
				path_order.append((pop_data, numeric_buffer))
				pop_data = num
			except IndexError:
				path_order.append((pop_data, numeric_buffer))
	return path_order


def decode_svg_path_string(pathString):
	token = _tokenize_path(pathString)
	path_order = list()
	d = token.next()
	while token:
		try:
			if d.isalpha():
				numeric_buffer = list()
				num = token.next()
				while not num.isalpha():
					numeric_buffer.append(float(num))
					num = token.next()
				path_order.append((d, numeric_buffer))
				d = num
		except Exception:
			path_order.append((d, numeric_buffer))
			break
	return path_order


def get_path_order_from_svg_file(svgFile):

	if not os.path.isfile(svgFile):
		print('ERROR: Svg file {} doest not exists!'.format(svgFile))
		return

	doc = minidom.parse(svgFile)
	style_type, styleRef = get_style_tag(doc)
	all_svg_tags = get_all_svg_tags(doc)
	result = list()

	for tag in all_svg_tags:
		id = tag.getAttribute('id').replace('_x5F_', '_')       # Get SVG layer name (id)
		if not id:
			id = None
		style_dict = dict()
		if style_type == 'styleElement' and tag.hasAttribute('class'):
			style = tag.getAttribute('class')
			if style in styleRef:
				style_dict = styleRef[style]
		elif style_type == 'styleAttribute':
			if tag.hasAttribute('style'):
				style = tag.getAttribute('style')
				style_dict = dict([s.split(':') for s in style.split(';') if s])
			else:
				for attr in ['fill', 'stroke', 'stroke-width', 'display']:
					if tag.hasAttribute(attr):
						style_dict[attr] = tag.getAttribute(attr)

		if tag.tagName == 'path':
			path = tag.getAttribute('d')
			path_order = decode_svg_path_string_replace(path)
		elif tag.tagName == 'circle':
			path_order = dict()
			path_order['cx'] = float(tag.getAttribute('cx'))
			path_order['cy'] = float(tag.getAttribute('cy'))
			path_order['rx'] = float(tag.getAttribute('r'))
			path_order['ry'] = float(tag.getAttribute('r'))
		elif tag.tagName == 'ellipse':
			path_order = {}
			path_order['cx'] = float(tag.getAttribute('cx'))
			path_order['cy'] = float(tag.getAttribute('cy'))
			path_order['rx'] = float(tag.getAttribute('rx'))
			path_order['ry'] = float(tag.getAttribute('ry'))
			path_order['transform'] = tag.getAttribute('transform') or ''
		elif tag.tagName == 'rect':
			path_order = {}
			x = tag.getAttribute('x')
			path_order['x'] = x and float(x) or 0.0
			y = tag.getAttribute('y')
			path_order['y'] = y and float(y) or 0.0
			path_order['w'] = float(tag.getAttribute('width'))
			path_order['h'] = float(tag.getAttribute('height'))
			rx = tag.getAttribute('rx')
			path_order['rx'] = rx and float(rx) or 0.0
			ry = tag.getAttribute('ry')
			path_order['ry'] = ry and float(ry) or 0.0
			path_order['transform'] = tag.getAttribute('transform') or ''
		elif tag.tagName == 'polygon':
			path_order = {}
			points = tag.getAttribute('points').strip()
			pnt = []
			for seg in points.split(' '):
				x, y = seg.split(',')
				pnt.append(QPointF(float(x), float(y)))
			path_order['points'] = pnt
		result.append((style_dict, path_order, tag.tagName, id))
	doc.unlink()
	return result


def create_svg_path(orders, verbose=False):
	path = QPainterPath()
	for k, order in enumerate(orders):
		if order[0] == 'M' or order[0] == 'm':
			if verbose:
				print(k, 'MOVE TO', order[1])
			move_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'C' or order[0] == 'c':
			if verbose:
				print(k, 'CUBIC TO', order[1])
			cubic_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'S' or order[0] == 's':
			if verbose:
				print(k, 'SMOOTH CUBIC TO', order[1])
			smooth_cubic_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'Q' or order[0] == 'q':
			if verbose:
				print(k, 'QUAD TO', order[1])
			quad_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'T' or order[0] == 't':
			if verbose:
				print(k, 'SMOOTH QUAD TO', order[1])
			smooth_quad_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'H' or order[0] == 'h':
			if verbose:
				print(k, 'HORIZONTAL LINE TO', order[1])
			horizontal_line_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'V' or order[0] == 'v':
			if verbose:
				print(k, 'VERTICAL LINE TO', order[1])
			vertical_line_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'L' or order[0] == 'l':
			if verbose:
				print(k, 'LINE TO', order[1])
			line_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'A' or order[0] == 'a':
			if verbose:
				print(k, 'ARC TO', order[1])
			arc_to(path, *order)
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif order[0] == 'z' or order[0] == 'Z':
			if verbose:
				print(k, 'close sub path')
			path.closeSubpath()
			if verbose:
				print(path.elementAt(path.elementCount() - 1).type)
		elif verbose:
			print(k, order)

	if verbose:
		print('------------end-------------')
	return path


def create_ellipse_path(data):
	path = QPainterPath()
	path.addEllipse(QPointF(data.get('cx'), data.get('cy')), data.get('rx'), data.get('ry'))
	if 'transform' in data:
		m = re.match('^matrix\\((.+)\\)$', data.get('transform'))
		if m:
			args = map(lambda x: float(x), m.group(1).split())
			if len(args) == 6:
				transform = QTransform(*args)
				path *= transform
	return path


def create_rect_path(data):
	path = QPainterPath()
	if data.get('rx') > 0 or data.get('ry'):
		path.addRoundedRect(data.get('x'), data.get('y'), data.get('w'), data.get('h'), data.get('rx'), data.get('ry'))
	else:
		path.addRect(data.get('x'), data.get('y'), data.get('w'), data.get('h'))
	if 'transform' in data:
		m = re.match('^matrix\\((.+)\\)$', data.get('transform'))
		if m:
			args = map(lambda x: float(x), m.group(1).split())
			if len(args) == 6:
				transform = QTransform(*args)
				path *= transform
	return path


def create_polygon_path(data):
	path = QPainterPath()
	polygon = QPolygonF()
	for pt in data.get('points'):
		polygon.append(pt)

	path.addPolygon(polygon)
	return path


def generate_path_to_svg(path):
	d = ''
	for i in range(path.elementCount()):
		element = path.elementAt(i)
		if element.type == QPainterPath.ElementType.MoveToElement:
			d += 'M%.3f,%.3f' % (element.x, element.y)
		elif element.type == QPainterPath.ElementType.CurveToElement:
			d += 'C%.3f,%.3f,' % (element.x, element.y)
		elif element.type == QPainterPath.ElementType.CurveToDataElement:
			d += '%.3f,%.3f' % (element.x, element.y)
			if path.elementAt(i + 1).type == QPainterPath.ElementType.CurveToDataElement:
				d += ','
		elif element.type == QPainterPath.ElementType.LineToElement:
			d += 'L%.3f,%.3f' % (element.x, element.y)
		else:
			print(element.type)

	d += 'Z'
	return d


def calculate_start_angle(x1, y1, rx, ry, coordAngle, largeArcFlag, sweep_flag, x2, y2):

	def dotproduct(v1, v2):
		return sum((a * b for a, b in zip(v1, v2)))

	def length(v):
		return math.sqrt(dotproduct(v, v))

	def angle(v1, v2):
		return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))

	rotated_x1 = math.cos(
		math.radians(coordAngle)) * ((x1 - x2) / 2) + math.sin(math.radians(coordAngle)) * ((y1 - y2) / 2)
	rotated_y1 = -math.sin(
		math.radians(coordAngle)) * ((x1 - x2) / 2) + math.cos(math.radians(coordAngle)) * ((y1 - y2) / 2)
	delta = rotated_x1 ** 2 / rx ** 2 + rotated_y1 ** 2 / ry ** 2
	if delta > 1:
		rx *= math.sqrt(delta)
		ry *= math.sqrt(delta)
	_a = (rx ** 2 * ry ** 2 - rx ** 2 * rotated_y1 ** 2 - ry ** 2 * rotated_x1 ** 2)
	_b = (rx ** 2 * rotated_y1 ** 2 + ry ** 2 * rotated_x1 ** 2)
	var = math.sqrt(_a / _b)
	if largeArcFlag == sweep_flag:
		var *= -1
	ccx = var * (rx * rotated_y1 / ry)
	ccy = var * -(ry * rotated_x1 / rx)
	cx = math.cos(math.radians(coordAngle)) * ccx - math.sin(math.radians(coordAngle)) * ccy + (x1 + x2) / 2
	cy = math.sin(math.radians(coordAngle)) * ccx + math.cos(math.radians(coordAngle)) * ccy + (y1 + y2) / 2
	start_angle = math.degrees(angle([1, 0], [(rotated_x1 - ccx) / rx, (rotated_y1 - ccy) / ry]))
	start_angle_sign = 1 * (rotated_y1 - ccy) / ry - 0 * (rotated_x1 - ccx) / rx
	if start_angle_sign == 0:
		start_angle_sign = 1.0
	start_angle_sign /= abs(start_angle_sign)
	start_angle *= start_angle_sign
	try:
		sweep_angle = math.degrees(
			angle([(rotated_x1 - ccx) / rx, (rotated_y1 - ccy) / ry],
				  [(-rotated_x1 - ccx) / rx, (-rotated_y1 - ccy) / ry]))
	except ValueError:
		sweep_angle = 180.0

	sweep_angle_sign = (rotated_x1 - ccx) / rx * (-rotated_y1 - ccy) / ry - \
					   (rotated_y1 - ccy) / ry * (-rotated_x1 - ccx) / rx
	if sweep_angle_sign == 0:
		sweep_angle_sign = 1.0
	sweep_angle_sign /= abs(sweep_angle_sign)
	sweep_angle *= sweep_angle_sign
	if sweep_flag == 0 and sweep_angle > 0:
		sweep_angle -= 360
	elif sweep_flag == 1 and sweep_angle < 0:
		sweep_angle += 360
	rect = QRectF(0, 0, rx * 2, ry * 2)
	rect.moveCenter(QPointF(cx, cy))
	return (start_angle, sweep_angle, rect)


def move_to(path, cmd, data):
	target = QPointF(*data)
	if cmd.islower():
		currentPos = path.currentPosition()
		target += currentPos
	path.moveTo(target)


def cubic_to(path, cmd, data):
	new1st_pos = QPointF(data[0], data[1])
	new2st_pos = QPointF(data[2], data[3])
	new_end_pos = QPointF(data[4], data[5])
	if cmd.islower():
		current_pos = path.currentPosition()
		new1st_pos += current_pos
		new2st_pos += current_pos
		new_end_pos += current_pos
	path.cubicTo(new1st_pos, new2st_pos, new_end_pos)


def smooth_cubic_to(path, cmd, data):
	elem_count = path.elementCount()
	prev_end_x, prevEndY = path.elementAt(elem_count - 1).x, path.elementAt(elem_count - 1).y
	prev2nd_x, prev2ndY = path.elementAt(elem_count - 2).x, path.elementAt(elem_count - 2).y
	new1st_pos = QPointF(2 * prev_end_x - prev2nd_x, 2 * prevEndY - prev2ndY)
	new2st_pos = QPointF(data[0], data[1])
	new_end_pos = QPointF(data[2], data[3])
	if cmd.islower():
		current_pos = path.currentPosition()
		new2st_pos += current_pos
		new_end_pos += current_pos
	path.cubicTo(new1st_pos, new2st_pos, new_end_pos)


def quad_to(path, cmd, data):
	new1st_pos = QPointF(data[0], data[1])
	new_end_pos = QPointF(data[2], data[3])
	path.quadTo(new1st_pos, new_end_pos)
	if cmd.islower():
		current_pos = path.currentPosition()
		new1st_pos += current_pos
		new_end_pos += current_pos
	path.quadTo(new1st_pos, new_end_pos)


def smooth_quad_to(path, cmd, data):
	elem_count = path.elementCount()
	prev_end_x, prevEndY = path.elementAt(elem_count - 1).x, path.elementAt(elem_count - 1).y
	prev1st_x, prev1stY = path.elementAt(elem_count - 2).x, path.elementAt(elem_count - 2).y
	new1st_pos = QPointF(2 * prev_end_x - prev1st_x, 2 * prevEndY - prev1stY)
	new_end_pos = QPointF(data[0], data[1])
	if cmd.islower():
		current_pos = path.currentPosition()
		new_end_pos += current_pos
	path.quadTo(new1st_pos, new_end_pos)


def horizontal_line_to(path, cmd, data):
	current_pos = path.currentPosition()
	if cmd.islower():
		target = current_pos + QPointF(data[0], 0)
	else:
		target = QPointF(data[0], current_pos.y())
	path.lineTo(target)


def vertical_line_to(path, cmd, data):
	current_pos = path.currentPosition()
	if cmd.islower():
		target = current_pos + QPointF(0, data[0])
	else:
		target = QPointF(current_pos.x(), data[0])
	path.lineTo(target)


def line_to(path, cmd, data):
	target = QPointF(*data)
	if cmd.islower():
		current_pos = path.currentPosition()
		target += current_pos
	path.lineTo(target)


def arc_to(path, cmd, data):
	current_pos = path.currentPosition()
	x1, y1 = current_pos.x(), current_pos.y()
	rx, ry, angle, fa, fs, x2, y2 = data
	if cmd.islower():
		x2 += x1
		y2 += y1
	start_angle, sweep_angle, rect = calculate_start_angle(x1, y1, rx, ry, angle, fa, fs, x2, y2)
	path.arcTo(rect, -start_angle, -sweep_angle)


def _tokenize_path(pathDef):
	for x in _COMMAND_RE.split(pathDef):
		if x in _COMMANDS:
			yield x
		for token in _FLOAT_RE.findall(x):
			yield token


def _tokenize_path_replace(path_def):
	path_def = path_def.replace('e-', 'NEGEXP').replace('E-', 'NEGEXP')
	path_def = path_def.replace(',', ' ').replace('-', ' -')
	path_def = path_def.replace('NEGEXP', 'e-')
	for c in _COMMANDS:
		path_def = path_def.replace(c, ' %s ' % c)
	return path_def.split()


class SvgParser(object):

	@staticmethod
	def get_svg_field_as_float(svg_field):
		"""
		Converts SVG field to a float value
		:param svg_field: object
		:return: float
		"""

		if not svg_field:
			svg_field = 0.0
		svg_field = str(svg_field)
		if 'px' in svg_field:
			svg_field = svg_field.strip('px')

		return float(svg_field)

	@staticmethod
	def get_width_from_svg_file(svg_path):
		"""
		Returns width of the given SVG file
		:param svg_path: str
		:return: float
		"""

		if not os.path.isfile(svg_path):
			LOGGER.warning(
				'Impossible to retrieve SVG width from file. SVG file "{}" does not exist!'.format(svg_path))
			return 0

		svg_obj = SvgParser.parse_svg(svg_path)
		svg_width = svg_obj.get_width()

		return svg_width

	@staticmethod
	def get_height_from_svg_file(svg_path):
		"""
		Returns height of the given SVG file
		:param svg_path: str
		:return: float
		"""

		if not os.path.isfile(svg_path):
			LOGGER.warning(
				'Impossible to retrieve SVG height from file. SVG file "{}" does not exist!'.format(svg_path))
			return 0

		svg_obj = SvgParser.parse_svg(svg_path)
		svg_height = svg_obj.get_height()

		return svg_height

	@staticmethod
	def get_size_from_svg_file(svg_path):
		"""
		Returns width and height of the given SVG file
		:param svg_path: str
		:return: tuple(float, float)
		"""

		svg_size = [0, 0]
		if not os.path.isfile(svg_path):
			LOGGER.warning('Impossible to retrieve SVG size from file. SVG file "{}" does not exist!'.format(svg_path))
			return svg_size

		svg_obj = SvgParser.parse_svg(svg_path)
		svg_size[0] = svg_obj.get_width()
		svg_size[1] = svg_obj.get_height()

		return svg_size

	@staticmethod
	def parse_svg(svg_path):
		"""
		Parses given SVG file
		:param svg_path: str
		:return: SVG object
		"""

		try:
			svg_obj = parser.parse(svg_path)
		except Exception as exc:
			raise Exception('{} | SVG file "{}" is not valid!'.format(exc, svg_path))

		return svg_obj

	@staticmethod
	def get_svg_element_font_size(svg_elem):
		"""
		Returns font size of the given SVG element
		:param svg_elem:
		:return: float
		"""

		if 'style' in svg_elem._attributes:
			match = re.search(r'(font\-size\:(\d+\.?\d*)px\;)', svg_elem._attributes['style'])
			if not match:
				return float(svg_elem._attributes['font-size'])
			else:
				return float(match.groups()[1])
		else:
			font_size = svg_elem._attributes['font-size']
			if font_size.endswith('px'):
				font_size = font_size.replace('px', '')

			return float(font_size)

	@staticmethod
	def set_svg_element_font_size(svg_elem, font_size):
		"""
		Sets font size of the given SVG element
		:param svg_elem:
		:param font_size: float
		"""

		if 'style' in svg_elem._attributes:
			match = re.search(r'(font\-size\:(\d+\.?\d*)px\;)', svg_elem._attributes['style'])
			if not match:
				svg_elem._attributes['font-size'] = font_size
			else:
				font_size_svg = match.groups()[0].replace(match.groups()[1], str(font_size))
				new_style = svg_elem._attributes['style'].replace(match.groups()[0], font_size_svg)
				svg_elem._attributes['style'] = new_style
		else:
			svg_elem._attributes['font-size'] = font_size

	@staticmethod
	def convert_svg_to_bitmap(source, target):
		svg_renderer = QSvgRenderer(source)
		height = svg_renderer.defaultSize().height()
		width = svg_renderer.defaultSize().width()
		new_image = QImage(width, height, QImage.Format_ARGB32)
		painter = QPainter(new_image)
		svg_renderer.render(painter)
		new_image.save(target)
		painter.end()


class SvgNormalizer(object):
	"""
	Normalizes each SVG element using original SVG resolution and new one
	"""

	def __init__(self, svg_elem, new_resolution, svg_original_resolution):

		self._new_resolution = new_resolution
		self._original_resolution = svg_original_resolution

		if svg_elem.__class__.__name__ == 'rect':
			self._normalize_rect(svg_elem)
		elif svg_elem.__class__.__name__ == 'tspan':
			self._normalize_tspan(svg_elem)
		elif svg_elem.__class__.__name__ == 'text':
			self._normalize_text(svg_elem)
		elif svg_elem.__class__.__name__ == 'line':
			self._normalize_line(svg_elem)
		elif svg_elem.__class__.__name__ == 'path':
			self._normalize_path(svg_elem)
		elif svg_elem.__class__.__name__ == 'image':
			self._normalize_image(svg_elem)

	def _normalize_position(self, svg_elem):
		x_pos = SvgParser.get_svg_field_as_float(svg_elem._attributes.get('x'))
		y_pos = SvgParser.get_svg_field_as_float(svg_elem._attributes.get('y'))
		original_position = [x_pos, y_pos]
		new_x = round(self._new_resolution[0] * float(original_position[0]) / float(self._original_resolution[0]))
		new_y = round(self._new_resolution[1] * float(original_position[1]) / float(self._original_resolution[1]))
		svg_elem.set_x(new_x)
		svg_elem.set_y(new_y)

	def _normalize_size(self, svg_elem):
		svg_width = SvgParser.get_svg_field_as_float(svg_elem._attributes.get('width'))
		svg_height = SvgParser.get_svg_field_as_float(svg_elem._attributes.get('height'))
		original_size = [svg_width, svg_height]
		new_width = (self._new_resolution[0] * float(original_size[0]) / float(self._original_resolution[0]))
		new_height = (self._new_resolution[1] * float(original_size[1]) / float(self._original_resolution[1]))
		svg_elem.set_width(new_width)
		svg_elem.set_height(new_height)

	def _normalize_rect(self, svg_rect_elem):
		self._normalize_position(svg_rect_elem)
		self._normalize_size(svg_rect_elem)

	def _normalize_tspan(self, svg_tspan_elem):
		self._normalize_position(svg_tspan_elem)

	def _normalize_text(self, svg_text_elem):
		self._normalize_position(svg_text_elem)
		res = OrderedDict()
		res[2048] = 1
		res[1920] = 1
		res[1600] = 0.936
		res[1500] = 0.936
		res[1033] = 0.78
		res[1024] = 0.78
		res[960] = 0.74
		res[768] = 0.66
		res[640] = 0.60

		new_width = float(self._new_resolution[0])
		font_size = SvgParser.get_svg_element_font_size(svg_text_elem)
		for i in range(len(res.keys())):
			if new_width > res.keys()[i]:
				if i == 0:
					font_proportion = new_width / res.keys()[0]
				else:
					size_per_pixel = (res[res.keys()[i - 1]] - res[res.keys()[i]]) / \
									 (res.keys()[i - 1] - res.keys()[i])
					font_proportion = (res[res.keys()[i]] + (new_width - res.keys()[i]) * size_per_pixel)
			break
		else:
			font_proportion = new_width * (res[res.keys()[
				len(res.keys()) - 1]] / res.keys()[len(res.keys()) - 1])

		new_font_size = font_size * font_proportion
		SvgParser.set_svg_element_font_size(svg_text_elem, new_font_size)

	def _normalize_line(self, svg_line_elem):
		x1_pos = SvgParser.get_svg_field_as_float(svg_line_elem._attributes.get('x1'))
		y1_pos = SvgParser.get_svg_field_as_float(svg_line_elem._attributes.get('y1'))
		original_position1 = [x1_pos, y1_pos]
		new_x1 = round(self._new_resolution[0] * float(original_position1[0]) / float(self._original_resolution[0]))
		new_y1 = round(self._new_resolution[1] * float(original_position1[1]) / float(self._original_resolution[1]))
		svg_line_elem._attributes['x1'] = new_x1
		svg_line_elem._attributes['y1'] = new_y1

		x2_pos = SvgParser.get_svg_field_as_float(svg_line_elem._attributes.get('x2'))
		y2_pos = SvgParser.get_svg_field_as_float(svg_line_elem._attributes.get('y2'))
		original_position2 = [x2_pos, y2_pos]
		new_x2 = round(self._new_resolution[0] * float(original_position2[0]) / float(self._original_resolution[0]))
		new_y2 = round(self._new_resolution[1] * float(original_position2[1]) / float(self._original_resolution[1]))
		svg_line_elem._attributes['x2'] = new_x2
		svg_line_elem._attributes['y2'] = new_y2

	def _normalize_path(self, svg_path_elem):
		path_x = float(svg_path_elem._attributes['d'].split(' ')[1].split(',')[0])
		path_y = float(svg_path_elem._attributes['d'].split(' ')[1].split(',')[1])
		dst_x = float(svg_path_elem._attributes['d'].split(' ')[2].split(',')[0])
		dst_y = float(svg_path_elem._attributes['d'].split(' ')[2].split(',')[1])
		width_proportion = (float(self._new_resolution[0]) / float(self._original_resolution[0]))
		height_proportion = (float(self._new_resolution[1]) / float(self._original_resolution[1]))
		new_path_x = path_x * width_proportion
		new_path_y = path_y * height_proportion
		new_dst_x = dst_x * width_proportion
		new_dst_y = dst_y * height_proportion
		new_d = 'm ' + str(new_path_x) + ', ' + str(new_path_y) + ' ' + str(new_dst_x) + ', ' + str(new_dst_y)
		svg_path_elem._attributes['d'] = new_d

	def _normalize_image(self, svg_image_elem):
		svg_width = SvgParser.get_svg_field_as_float(svg_image_elem._attributes.get('width'))
		svg_height = SvgParser.get_svg_field_as_float(svg_image_elem._attributes.get('height'))
		original_size = [svg_width, svg_height]
		aspect_ratio = float(svg_width) / float(svg_height)
		new_width = round(self._new_resolution[0] * float(original_size[0]) / float(self._original_resolution[0]))
		new_height = float(new_width) / aspect_ratio
		svg_image_elem.set_width(new_width)
		svg_image_elem.set_height(new_height)

		x_pos = SvgParser.get_svg_field_as_float(svg_image_elem._attributes.get('x'))
		y_pos = SvgParser.get_svg_field_as_float(svg_image_elem._attributes.get('y'))
		original_position = [x_pos, y_pos]
		x_dst_proportion = float(svg_width) / (float(original_position[0]) - x_pos)
		y_dst_proportion = float(svg_height) / (float(original_position[1]) - y_pos)
		new_x = self._new_resolution[0] - (new_width / x_dst_proportion)
		new_y = self._new_resolution[1] - (new_height / y_dst_proportion)
		svg_image_elem.set_x(new_x)
		svg_image_elem.set_y(new_y)
