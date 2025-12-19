from __future__ import annotations

import logging
import marshal
import subprocess
import typing
from typing import Final

from .errors import CommandExecutionError, ConnectionExpiredError
from .helpers import StrEnum
from .message import MessageSeverity
from .models import ActionInfo, ActionMessage, PerforceDict

if typing.TYPE_CHECKING:
    from .connection import Connection

logger: Final = logging.getLogger(__name__)


class MarshalCode(StrEnum):
    """Represents the values of the `code` field from a marshaled P4 response.

    This class is derived from `StrEnum` and is used to define the possible
    values for the `code` field in output dictionaries from the `p4 -G`
    command. Each value has specific semantics representing the state of
    the marshaled response.

    Attributes:
        STAT: Indicates a status code. Represents the default response state.
        ERROR: Indicates an error occurred in the response. The associated
            'data' field in the output contains the detailed error message.
        INFO: Indicates informational feedback from the command. The
            corresponding 'data' field contains the feedback message.
    """

    """Values of the ``code`` field from a marshaled P4 response.

    The output dictionary from ``p4 -G`` must have a ``code`` field.
    """

    STAT = "stat"
    ERROR = "error"
    INFO = "info"


def p4(
    connection: Connection,
    command: list[str],
    stdin: PerforceDict | None = None,
    max_severity: MessageSeverity = MessageSeverity.EMPTY,
) -> list[PerforceDict]:
    """Run a ``p4`` command and return its output.

    This function uses `marshal` (using ``p4 -G``) to load stdout and dump stdin.

    Args:
        connection: The connection to execute the command with.
        command: A ``p4`` command to execute, with arguments.
        stdin: Write a dict to the standard input file using `marshal.dump`.
        max_severity: Raises an exception if the output error severity is above
            that threshold.

    Returns:
        The command output.

    Raises:
        CommandExecutionError: An error occured during command execution.
        ConnectionExpiredError: Connection to server expired, password is required.
            You can use the `login` function.
    """

    args = ["p4", "-G", "-p", connection.port]
    if connection.user:
        args.extend(("-u", connection.user))
    if connection.client:
        args.extend(("-c", connection.client))
    args.extend(command)

    logger.debug("Running: '%s'", " ".join(args))

    result: list[PerforceDict] = []
    # Cache enum values for faster comparison in the loop
    error_code: str = MarshalCode.ERROR.value
    max_severity_val: int = int(max_severity)

    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE if stdin else None,
        stderr=subprocess.PIPE,
    )
    with process:
        if stdin:
            assert process.stdin is not None  # noqa: S101
            marshal.dump(
                stdin, process.stdin, 0
            )  # NOTE: perforce require version 0
            process.stdin.close()

        assert process.stdout is not None  # noqa: S101
        while True:
            try:
                out: dict[bytes, bytes | int] = marshal.load(process.stdout)  # noqa: S302
            except EOFError:
                break

            # NOTE: Some rare values, like user FullName, can be encoded
            # differently, and decoding them with 'latin-1' give us a result
            # that seem to match what P4V does.
            data: PerforceDict = {
                key.decode(): val.decode("latin-1")
                if isinstance(val, bytes)
                else str(val)
                for key, val in out.items()
            }

            code = data.get("code")
            if code == error_code:
                severity = int(data.get("severity", 0))
                if severity > max_severity_val:
                    message = data.get("data", "").strip()

                    if (
                        message
                        == "Perforce password (P4PASSWD) invalid or unset."
                    ):
                        raise ConnectionExpiredError(
                            "Perforce connection expired, password is required"
                        )

                    raise CommandExecutionError(
                        message, command=args, data=data
                    )

            result.append(data)

        _, stderr = process.communicate()
        if stderr:
            message = stderr.decode()
            raise CommandExecutionError(message, command=args)

    return result


def add(
    connection: Connection,
    file_specs: list[str],
    *,
    changelist: int | None = None,
    preview: bool = False,
) -> tuple[list[ActionMessage], list[ActionInfo]]:
    """Add files to version control.

    Notes:
        The user can optionally specify a changelist to associate with these files and can
        execute a preview without making actual changes.

    Args:
        connection: The connection object representing the established
            connection to the version control system.
        file_specs: A list of file specifications to be added.
        changelist: The ID of the changelist to associate with the files.
        preview: If `True`, performs a preview of the add command without executing it.

    Returns:
        A tuple containing a list of action messages and a list of action information objects
        relevant to the operation.
    """

    command = ["add"]
    if changelist:
        command.extend(("-c", str(changelist)))
    if preview:
        command.append("-n")
    command.extend(file_specs)

    messages: list[ActionMessage] = []
    infos: list[ActionInfo] = []
    info_code: str = MarshalCode.INFO.value
    for data in p4(connection, command):
        if data.get("code") == info_code:
            messages.append(ActionMessage.from_info_data(data))
        else:
            infos.append(ActionInfo(**data))

    return messages, infos
