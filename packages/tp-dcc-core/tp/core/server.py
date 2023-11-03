#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that tp-dcc-tools Server implementation.
"""

from __future__ import annotations

import sys
import json
import time
import socket
import inspect
import traceback
import importlib
import urllib.parse
import multiprocessing
from http import server
from functools import partial
from datetime import datetime
from typing import Callable, Any
from types import ModuleType, FunctionType

from Qt.QtCore import QObject, Signal, QThread

from tp.core import log, dcc
from tp.modules import core

if dcc.is_maya():
    import maya.utils

logger = log.tpLogger


def port_in_use(port: int, host: str = '127.0.0.1') -> bool:
	"""
	Returns whether given port is already in use by a different process. Useful if you cna start a server on a default
	port that might already be in use.

	:param int port: port number to check.
	:param str host: host name.
	:return: True if port is being used by another process; False otherwise.
	:rtype: bool
	"""

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(0.125)
	result = sock.connect_ex((host, port))

	return True if result == 0 else False


def start_server_in_thread(
		host_program: str = '', host: str = '127.0.0.1', port: int | None = None, load_modules: list[str | ModuleType] = None,
		echo_response: bool = False) -> tuple[QThread | None, Server | None]:
	"""
	Starts a server in a separated QThread.

	:param host_program:
	:param host:
	:param port:
	:param load_modules:
	:param echo_response:
	:return:
	"""

	def _kill_thread(_thread: QThread, _):
		_thread.exit()
		logger.info('DCC server thread was killed!')

	host_program = host_program or dcc.name()
	port = port or dcc.dcc_port(host_program)

	if port_in_use(port=port, host=host):
		logger.error(f'Port {port} is already in use, cannot start server!')
		return None, None

	new_server = Server(
		host_program=host_program, host_address=host, port=port, load_modules=load_modules, use_main_thread_executor=False,
		echo_response=echo_response)
	thread_object = QThread()
	new_server.isTerminated.connect(partial(_kill_thread, thread_object))
	new_server.moveToThread(thread_object)
	thread_object.started.connect(new_server.start_listening)
	thread_object.start()

	return thread_object, new_server


class Server(QObject):
	"""
	Main DCC server class
	"""

	class Errors:
		"""
		Class that stores all server related error messages.
		"""

		CALLING_FUNCTION = 'ERROR 0x1: An error occurred when calling the function'
		IN_FUNCTION = 'ERROR 0x2: An error occurred when executing the function'
		SERVER_COMMAND = 'ERROR 0x3: An error occurred processing this server command'
		SERVER_RELOAD = 'ERROR 0x4: An error occurred with reloading a module on the server'
		TIMEOUT = 'ERROR 0x5: The command timed out'
		NO_RESPONSE = 'ERROR 0x7: No response was generated, is the function on the server returning anything?'

	class Commands:
		"""
		Commands that are not run from any modules, but in the server class.
		"""

		TP_DCC_SHUTDOWN = 'TP_DCC_SHUTDOWN'
		TP_DCC_LS = 'TP_DCC_LS'
		TP_DCC_RELOAD_MODULES = 'TP_DCC_RELOAD_MODULES'
		TP_DCC_LOAD = 'TP_DCC_LOAD'
		TP_DCC_UNLOAD = 'TP_DCC_UNLOAD'
		TP_DCC_FUNCTION_HELP = 'TP_DCC_FUNCTION_HELP'

	isTerminated = Signal(str)
	commandToBeExecuted = Signal(str, dict)
	commandExecuted = Signal(str, dict)

	def __init__(
			self, host_program: str | None = None, host_address: str = '127.0.0.1', port: int | None = None,
			load_modules: list[str | ModuleType] | None = None, use_main_thread_executor: bool = False,
			echo_response: bool = True):
		super().__init__()

		self._host_program = host_program or dcc.name()
		self._host_address = host_address
		self._port = port or dcc.dcc_port(host_program)
		self._use_main_thread_executor = use_main_thread_executor
		self._echo_response = echo_response
		self._keep_running = True
		self._executor_reply: dict | None = None
		self._http_server: server.HTTPServer | None = None
		self._loaded_modules: dict[str, list[ModuleType]] = {'internal': [core]}
		for module_name in load_modules or list():
			self.load_module(module_name)

	def start_listening(self):
		"""
		Starts to server to listen for incoming requests. Server will keep listening for requests until keep_running
		is False.
		"""

		def _handler(*args):
			return ServerHTTPRequestHandler(dcc_server=self, *args)

		self._http_server = server.HTTPServer((self._host_address, self._port), _handler)
		logger.info(f'Started DCC Server on address: {self._host_address}:{self._port}')
		while self._keep_running:
			self._http_server.handle_request()
		logger.info('Shutting down server')
		self._http_server.server_close()
		logger.info('Server shut down')

	def stop_listening(self):
		"""
		Stops listening for incoming requests.
		"""

		self._keep_running = False
		self._http_server.server_close()
		self.isTerminated.emit('TERMINATED')

	def load_module(self, module_name: str | ModuleType, namespace: str | None = None, is_internal_module: bool = False):
		"""
		Tries to load a module with the given name, while server is running.

		:param str module_name: name of the module to load.
		:param str or None namespace:optional namespace that will be used to register module into.
		:param bool is_internal_module: whether the module to load is an internal one. Internal modules will be
			imported from tp namespace.
		:return: True if the module was loaded successfully; False otherwise.
		:rtype: bool
		"""

		if isinstance(module_name, ModuleType):
			module_name = module_name.__name__ if not is_internal_module else module_name.__name__.split('.')[-1]

		try:
			if is_internal_module:
				namespace = 'internal'
				mod = importlib.import_module(f'tp.modules.{module_name}', package='tp')
			else:
				mod = importlib.import_module(module_name)
			namespace = namespace or 'default'
			self._loaded_modules.setdefault(namespace, [])
			if mod not in self._loaded_modules[namespace]:
				self._loaded_modules[namespace].append(mod)
				logger.debug(f'Added {namespace}:{mod}')
				logger.debug(self._loaded_modules)
				return True
		except Exception as err:
			logger.error(f'Failed to hot load module: {module_name}: {err}')

		return False

	def unload_module(self, module_name: str, is_internal_module: bool = True) -> bool:
		"""
		Removes a module from the server.

		:param str module_name: name of the module to load.
		:param bool is_internal_module: whether the module to load is an internal one. Internal modules will be
			retrieved from tp namespace.
		:return: True if the module was unloaded successfully; False otherwise.
		:rtype: bool
		"""

		full_name = f'tp.modules.{module_name}' if is_internal_module else module_name
		for module in self._loaded_modules:
			if module.__name__ == full_name:
				self._loaded_modules.remove(module)
				return True

		return False

	def reload_modules(self, namespace: str | None = None) -> list[str]:
		"""
		Reloads all the currently loaded modules.

		:param str or None namespace:optional namespace that will be used to register module into.
		:return: list of reloaded module names.
		"""

		reloaded_modules = []
		for key, modules in self._loaded_modules.items():
			if namespace and key != namespace:
				continue
			for module in modules:
				importlib.reload(module)
				reloaded_modules.append(module.__name__)

		return reloaded_modules

	def function_by_name(
			self, function_name, module_name: str | None = None, namespace: str | None = None) -> Callable | None:
		"""
		Tries to find a function by its given name.

		:param str function_name: name of the function to retrieve.
		:param str or None module_name: optional name of the module to search function in. If not given, all modules
			will be searched.
		:param str or None namespace: optional namespace that will be used to find module from.
		:return: function that matches the given name.
		:rtype: Callable or None
		"""

		if module_name is not None:
			module = sys.modules.get(f'.modules.{module_name}')
			if module is not None:
				modules = {'internal': [module]}
			else:
				module = sys.modules.get(module_name)
				modules = {'internal': [module]}
		else:
			modules = self._loaded_modules

		found_function = None
		for key, mods in modules.items():
			if namespace and namespace != key:
				continue
			if found_function is not None:
				break
			for module in mods:
				for name, value in module.__dict__.items():
					if callable(value):
						if function_name == name:
							found_function = value
							break

		return found_function

	def filter_and_execute_function(self, function_name: str, parameters: dict) -> bytes:
		"""
		Function that decides whether the function call should come from one of the loaded modules or from the server.

		:param str function_name: name of the function to execute.
		:param dict parameters: parameters to pass to the function.
		:return: function call output.
		:rtype: bytes
		..note:: server commands should start with TP_DCC_
		..warning:: this function should not be called directly.
		"""

		if function_name in dir(Server.Commands):
			result = self._process_server_command(function_name, parameters)
		else:
			result = self._process_module_command(function_name, parameters)

		self._executor_reply = None
		return json.dumps(result).encode()

	def _make_result(self, success: bool, return_value: Any, message: str = '', command: str | None = None) -> dict:
		"""
		Internal function that constructs a JSON for the server to send back after a POST request.

		:param bool success: whether the result was a success.
		:param Any return_value: result value.
		:param str command: name of the executed command.
		:return: JSON server dictionary.
		:rtype: dict
		"""

		return {
			'Time': datetime.now().strftime('%H:%M:%S'),
			'Success': success,
			'ReturnValue': return_value,
			'Message': message,
			'Command': command,
			'PID':multiprocessing.current_process().pid
		}

	def _process_server_command(self, function_name: str, parameters: dict) -> dict:
		"""
		Internal function that processes internal functions.

		:param str function_name: name of the server function to call.
		:param dict parameters: parameters to pass to the function.
		:return: server command function call output.
		:rtype: dict
		"""

		result = self._make_result(success=False, return_value=None, message=Server.Errors.SERVER_COMMAND, command=None)

		if function_name == Server.Commands.TP_DCC_SHUTDOWN:
			self.stop_listening()
			result = self._make_result(
				success=True, return_value=True, message='Server offline', command=Server.Commands.TP_DCC_SHUTDOWN)
		elif function_name == Server.Commands.TP_DCC_LS:
			functions = []
			for module in self._loaded_modules:
				functions.extend([func for func in dir(module) if '__' not in func or isinstance(func, FunctionType)])
			result = self._make_result(success=True, return_value=functions, command=Server.Commands.TP_DCC_LS)
		elif function_name == Server.Commands.TP_DCC_RELOAD_MODULES:
			reloaded_modules = self.reload_modules()
			result = self._make_result(
				success=True, return_value=reloaded_modules, command=Server.Commands.TP_DCC_RELOAD_MODULES)
		elif function_name == Server.Commands.TP_DCC_LOAD:
			modules = parameters.get('_Module', [])
			is_internal_module = parameters.get('is_internal_module', True)
			loaded_modules = []
			for module_name in modules:
				try:
					self.load_module(module_name, is_internal_module=is_internal_module)
					loaded_modules.append(module_name)
				except Exception:
					logger.info('An error occurred processing this server command', module_name)
					logger.info(traceback.format_exc())
			result = self._make_result(success=True, return_value=loaded_modules, command=Server.Commands.TP_DCC_LOAD)
		elif function_name == Server.Commands.TP_DCC_UNLOAD:
			modules = parameters.get('_Module', [])
			for module_name in modules:
				self.unload_module(module_name)
			result = self._make_result(
				success=True,
				return_value=[m.__name__ for m in self._loaded_modules], command=Server.Commands.TP_DCC_UNLOAD)
		elif function_name == Server.Commands.TP_DCC_FUNCTION_HELP:
			function_name = parameters.get('FunctionName')
			function = self.function_by_name(function_name)
			arg_spec = inspect.getfullargspec(function)
			arg_spec_dict = {
				'FunctionName': function_name,
				'Arguments': arg_spec.args
			}
			if arg_spec.varargs is not None:
				arg_spec_dict['PackedArgs'] = f'*{arg_spec.varargs}'
			if arg_spec.varkw is not None:
				arg_spec_dict['PackedKwargs'] = f'**{arg_spec.varkw}'
			result = self._make_result(
				success=True, return_value=arg_spec_dict, command=Server.Commands.TP_DCC_FUNCTION_HELP)

		self.commandExecuted.emit(function_name, result)
		logger.debug(f'Executed {function_name}')

		return result

	def _process_module_command(
			self, function_name: str, parameters: dict, namespace: str | None = None, timeout: float = 10.0) -> dict:
		"""
		Processes a command if the function it was a module function.

		:param str function_name: name of module function to call.
		:param dict parameters: parameters to pass to the function.
		:param str or None namespace: optional namespace that will be used to find module from.
		:param timeout: time out function call.
		:return: module command function call output.
		:rtype: dict
		"""

		if self._use_main_thread_executor:
			self.commandToBeExecuted.emit(function_name, parameters)
			start_time = time.time()

			# wait for the executor to reply until time out.
			while self._executor_reply is None:
				current_time = time.time()
				if current_time - start_time > timeout:
					self._executor_reply = self._make_result(
						success=False, return_value=None, message=Server.Errors.TIMEOUT, command=function_name)
			return self._executor_reply

		module = parameters.pop('_Module', None)
		function = self.function_by_name(function_name, module_name=module, namespace=namespace)
		if not function:
			msg = f'No function with name {function_name} loaded within TNM Dcc hook server'
			if namespace:
				msg = f'No function with name {function_name} within {namespace} loaded within DCC Server'
			result = self._make_result(success=False, return_value=None, message=msg, command=function_name)
			return result

		message = ''
		try:
			return_value = function(**parameters)
			success = True
			self.commandExecuted.emit(function_name, parameters)
		except Exception as err:
			logger.error(err)
			return_value = None
			message = str(traceback.format_exc())
			success = False

		return self._make_result(success=success, return_value=return_value, message=message, command=function_name)


class ServerHTTPRequestHandler(server.BaseHTTPRequestHandler):
	"""
	Class that handles requests coming into the server.
	"""

	def __init__(
			self, request: bytes, client_address: tuple[str, int], server: 'BaseServer',
			dcc_server: Server | None = None, reply_with_auto_close: bool = True):

		self._dcc_server = dcc_server
		self._reply_with_auto_close = reply_with_auto_close

		super().__init__(request, client_address, server)

	def send_response_data(self, request_type: str):
		"""
		Generates the response and appropriate headers to send back to the client.

		:param str request_type: GET or POST.
		"""

		self.send_response(200)
		header = {'GET': 'text/html', 'POST': 'application/json'}.get(request_type, None)
		if header:
			self.send_header('Content-type', header)
		self.end_headers()

	def do_GET(self):
		"""
		Handles a GET request.
		"""

		# browsers tend to send a GET for the favicon as well, which we don't care about
		if self.path == "/favicon.ico":
			return

		data = urllib.parse.unquote(self.path).lstrip('/')
		parts = data.split('&')

		try:
			function = eval(parts[0])
			parameters = json.loads(parts[1]) or dict()
		except NameError as err:
			logger.warning(f'Got a GET request that I do not know what to do with')
			logger.warning(f'Request was: GET {data};')
			logger.warning(f'Error is   : {err}')
			return

		command_response = self._dcc_server.filter_and_execute_function(function, parameters)
		self.send_response_data('GET')
		self.wfile.write(bytes(f'{command_response}'.encode('utf-8')))
		if self._reply_with_auto_close:
			# reply back to the browser with a javascript that will close the window (tab) it just opened
			self.wfile.write(
				bytes("<script type='text/javascript'>window.open('','_self').close();</script>".encode('utf-8')))

	def do_POST(self):
		"""
		Handles a POST request and expects a JSON object to be sent in the POST data.
		"""

		data = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
		function = data.get('FunctionName')
		parameters = data.get('Parameters') or dict()
		if dcc.is_maya():
			command_response = maya.utils.executeInMainThreadWithResult(
				self._dcc_server.filter_and_execute_function, function, parameters)
		else:
			command_response = self._dcc_server.filter_and_execute_function(function, parameters)
		self.send_response_data('POST')
		self.wfile.write(command_response)
