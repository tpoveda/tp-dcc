from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .helpers import StrEnum
from .message import MessageLevel

PerforceDict = dict[str, str]


class PyforceModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __repr_args__(self) -> Iterable[tuple[str | None, Any]]:
        """Generate iterable of key-value pairs for representation purposes.

        This method overrides the `__repr_args__` method for objects. It filters out
        keys that belong to the extra fields managed by the class (if any), while
        keeping the base class's argument representation intact.

        Returns:
            An iterable containing key-value pairs of arguments for the representation, excluding
            any filtered-out keys.
        """

        extra = self.__pydantic_extra__
        if not extra:
            return super().__repr_args__()
        return (
            (key, val)
            for (key, val) in super().__repr_args__()
            if key not in extra
        )


class Action(StrEnum):
    """Enumerator with all available Perforce actions."""

    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    BRANCH = "branch"
    MOVE_ADD = "move/add"
    MOVE_DELETE = "move/delete"
    INTEGRATE = "integrate"
    IMPORT = "import"
    PURGE = "purge"
    ARCHIVE = "archive"


@dataclass(frozen=True, slots=True)
class ActionMessage:
    """Represent a message associated with an action, including its path, content, and severity level.

    This class is intended to encapsulate messages associated with specific actions. Each message
    consists of a `path`, the `message` content itself, and its severity `level`.

    Attributes:
        path: The path associated with the action message.
        message: The content of the action message.
        level: The severity level of the action message.
    """

    path: str
    message: str
    level: MessageLevel

    @classmethod
    def from_info_data(cls, data: PerforceDict) -> ActionMessage:
        """Create an instance of `ActionMessage` from a dictionary of information data.

        Args:
            data: The dictionary containing the information data.

        Returns:
            An instance of ActionMessage constructed from the provided information data.
        """

        path, _, message = data["data"].rpartition(" - ")
        level = MessageLevel(int(data["level"]))
        return cls(
            path=path.strip(),
            message=message.strip(),
            level=level,
        )


class ActionInfo(PyforceModel):
    """Represent information about an action performed on a file.

    This class defines the data structure for storing details related to an
    action performed on a file within a version control system. It contains
    attributes for the action type, file paths, file type, and the working
    revision of the file.

    Attributes:
        action: The type of action performed (e.g., add, edit, delete).
        client_file: The path of the file on the client machine.
        depot_file: The path of the file in the depot.
        file_type: The type and attributes of the file in the version control system.
        work_rev: The revision number of the file being worked on.
    """

    action: str
    client_file: str = Field(alias="clientFile")
    depot_file: str = Field(alias="depotFile")
    file_type: str = Field(alias="type")
    work_rev: int = Field(alias="workRev")
