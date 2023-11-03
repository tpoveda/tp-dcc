#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that tp-dcc-tools Client implementations for different DCCs
"""

from __future__ import annotations

import pprint
import requests

from overrides import override

from tp.core import log, dcc, dccs

logger = log.tpLogger


class AbstractClient:
    """
    Base DCC client class
    """

    class CantReacherServer(Exception):
        pass

    def __init__(
            self, port: int = dccs.Ports['Undefined'], host_address: str = '127.0.0.1',
            host_program: str = dccs.Standalone):
        super().__init__()

        self._port = port
        self._host_address = host_address
        self._timeout = 1000
        self._echo_execution = True
        self._echo_payload = True
        self._is_executing = False
        self._host_program = host_program

    def is_executing(self) -> bool:
        """
        Returns whether client is still executing a command.

        :return: True if client is running a command; False otherwise.
        :rtype: bool
        """

        return self._is_executing

    def is_host_online(self) -> bool:
        """
        Returns whether host is online.

        Returns:
            bool: True if host is online; False otherwise.
        """

        try:
            result = self.execute('is_online', {})
            return result.get('Success', False) or result.get('ReturnValue', False)
        except AbstractClient.CantReacherServer:
            return False
        except RuntimeError as err:
            logger.error(err)
            return False

    def echo_payload(self) -> bool:
        """
        Returns whether JSON payload sent to the server are printed in the client output.

        :return: True if JSON payload is printed in the client output; False otherwise.
        :rtype: bool
        """

        return self._echo_payload

    def set_echo_payload(self, flag: bool):
        """
        Sets whether client will print JSON payload sent to the server in the client output.

        :param bool flag: True to print JSON payload in the client output; False otherwise.
        """

        self._echo_payload = flag

    def echo_execution(self) -> bool:
        """
        Returns whether responses from server are printed in the client output.

        :return: True if server response is printed in the client output; False otherwise.
        :rtype: bool
        """

        return self._echo_execution

    def set_echo_execution(self, flag: bool):
        """
        Sets whether responses from server are printed in the client output.

        :param bool flag: True to print server response in the client output; False otherwise.
        """

        self._echo_execution = flag

    def timeout(self) -> float:
        """
        Returns the current timeout value.

        :return: timeout value in seconds.
        :rtype: float
        """

        return self._timeout

    def set_timeout(self, value: float):
        """
        Sets time out the connection to the server after this value in seconds.

        :param float value: time out value in seconds.
        """

        self._timeout = value

    def execute(self, command: str | callable, parameters: dict | None = None, timeout: float = 0.0) -> dict:
        """
        Executes given command for this client. The server will look for this command in the modules it has
        loaded.

        :param str or callable command: command name or the actual function object that you can import from the
            available server modules.
        :param dict or None parameters: parameters to pass to the command. These must match the argument names of the
            function that will be executed.
        :param float timeout: optional time in seconds after which the request will time out. If not given, default time
            out will be used.
        :return: response coming from the server.
            {
                'returnValue': ['Camera', 'Cube'],
                'success': True
            }
        :rtype: dict
        :raises Client.CantReacherServer: if client cannot reach server.
        """

        try:
            self._is_executing = True
            timeout = timeout if timeout > 0 else self._timeout
            command = command.__name__ if callable(command) else command
            url = f'http://{self._host_address}:{self._port}'
            payload = self._create_payload(command, parameters)

            try:
                response = requests.post(url, json=payload, timeout=timeout).json()
            except requests.exceptions.ConnectionError as err:
                raise AbstractClient.CantReacherServer(f'Cannot reach server {self._host_address} on port {self._port}')

            if self.echo_payload():
                pprint.pprint(payload)
            if self.echo_execution():
                pprint.pprint(response)
        finally:
            self._is_executing = False

        return response

    def _create_payload(self, command_name: str, parameters: dict):
        """
        Internal function that constructs the dictionary for the JSON payload that will be sent to the server.

        :param str command_name: name of the command to run.
        :param dict or None parameters: parameters to pass to the command. These must match the argument names of the
            function that will be executed.
        :return: command payload.
        :rtype: dict
        """

        return {
            'FunctionName': command_name,
            'Parameters': parameters
        }


class MayaClient(AbstractClient):
    """
    Custom client for Maya
    """

    def __init__(self, port: int = dcc.dcc_port(dccs.Maya), host_address: str = '127.0.0.1'):
        super().__init__(port=port, host_address=host_address, host_program=dccs.Maya)


class MaxClient(AbstractClient):
    """
    Custom client for 3ds Max
    """

    def __init__(self, port: int = dcc.dcc_port(dccs.Max), host_address: str = '127.0.0.1'):
        super().__init__(port=port, host_address=host_address, host_program=dccs.Max)


class BlenderClient(AbstractClient):
    """
    Custom client for Blender
    """

    def __init__(self, port: int = dcc.dcc_port(dccs.Blender), host_address: str = '127.0.0.1'):
        super().__init__(port=port, host_address=host_address, host_program=dccs.Blender)


class HoudiniClient(AbstractClient):
    """
    Custom client for Houdini
    """

    def __init__(self, port: int = dcc.dcc_port(dccs.Houdini), host_address: str = '127.0.0.1'):
        super().__init__(port=port, host_address=host_address, host_program=dccs.Houdini)
        self._host_program = dccs.Houdini


class UnrealClient(AbstractClient):
    """
    Custom client for Unreal Engine
    """

    def __init__(self, port: int = dcc.dcc_port(dccs.Unreal), host_address: str = '127.0.0.1'):
        super().__init__(port=port, host_address=host_address, host_program=dccs.Unreal)

        self._command_object_path = '/Engine/PythonTypes.Default__tpDccCommands'
        self._server_command_object_path = '/Engine/PythonTypes.Default__tpDccServerCommands'
        self._headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    @override
    def execute(self, command: str or callable, parameters: dict or None = None, timeout: float = 0.0) -> dict:

        try:
            self._is_executing = True
            timeout = timeout if timeout > 0 else self._timeout
            url = f'http://{self._host_address}:{self._port}/remote/object/call'
            payload = self._create_payload(command, parameters, self._command_object_path)

            if self.echo_payload():
                pprint.pprint(payload)

            try:
                response  = requests.put(url, json=payload, headers=self._headers, timeout=timeout).json()
            except requests.exceptions.ConnectionError:
                raise AbstractClient.CantReacherServer(
                    'Cannot connect to Unreal, check Unreal is running and Remote Control API plugin is loaded')

            try:
                response = {'ReturnValue': eval(response.get('ReturnValue'))}
            except Exception:
                pass

            if self.echo_execution():
                pprint.pprint(response)

            return response
        finally:
            self._is_executing = False

    @override(check_signature=False)
    def _create_payload(self, command_name: str, parameters: dict, object_path: str):
        return {
            'FunctionName': command_name,
            'ObjectPath': object_path,
            'Parameters': parameters,
            'GenerateTransaction': True
        }
