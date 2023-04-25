#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils functions and classes
"""

from tp.common.nodegraph.core import consts


def format_color(clr):
	if isinstance(clr, str):
		clr = clr.strip('#')
		return tuple(int(clr[i:i + 2], 16) for i in (0, 2, 4))
	return clr


class ClassProperty(object):

	def __init__(self, f):
		self.f = f

	def __get__(self, instance, owner):
		return self.f(owner)


def acyclic_check(start_socket_view, end_socket_view):
	"""
	Validates whether the given sockets can be connected.

	:param tp.common.noddegraph.views.socket.SocketView start_socket_view: start socket view.
	:param tp.common.noddegraph.views.socket.SocketView end_socket_view: end socket view.
	:return: True if socket connections is valid; False otherwise.
	:rtype: bool
	"""

	start_node = start_socket_view.node
	check_nodes = [end_socket_view.node]

	io_types = {
		consts.SocketDirection.Input: 'outputs',
		consts.SocketDirection.Output: 'inputs'
	}

	while check_nodes:
		check_node = check_nodes.pop(0)
		for check_socket in getattr(check_node, io_types[end_socket_view.direction]):
			for socket in check_socket.connected_sockets:
				if socket.node != start_node:
					check_nodes.append(socket.node)
				else:
					return False

	return True


def can_connect_ports(start_socket_view, end_socket_view):
	"""
	Returns whether the connection between two given socket views its possible.

	:param tp.common.noddegraph.views.socket.SocketView start_socket_view: start socket view.
	:param tp.common.noddegraph.views.socket.SocketView end_socket_view: end socket view.
	:return: True ifsocket connections is valid; False otherwise.
	:rtype: bool
	"""

	if start_socket_view is None or end_socket_view is None:
		return False

	if start_socket_view.direction == end_socket_view.direction:
		return False

	if start_socket_view.node == end_socket_view.node:
		return False

	if not acyclic_check(start_socket_view, end_socket_view):
		return False

	return True


def compute_node_rank(nodes, down_stream=True):
	"""
	Computes the ranking of nodes.

	:param list[tp.common.nodegraph.core.node.BaseNode] nodes: nodes to start ranking from.
	:param bool down_stream: whether to compute down stream.
	:return: computed node rank.
	:rtype: dict
	"""

	def _update_node_rank(_node, _nodes_rank, _down_stream=True):
		node_values = _node.connected_output_nodes().values() if down_stream else _node.connected_input_nodes().values()
		connected_nodes = set()
		for _nodes in node_values:
			connected_nodes.update(_nodes)
		rank = _nodes_rank[_node] + 1
		for n in connected_nodes:
			if n in _nodes_rank:
				_nodes_rank[n] = max(_nodes_rank[n], rank)
			else:
				_nodes_rank[n] = rank
			_update_node_rank(n, _nodes_rank, _down_stream)

	nodes_rank = dict()
	for node in nodes:
		nodes_rank[node] = 0
		_update_node_rank(node, nodes_rank, down_stream)

	return nodes_rank

