from __future__ import annotations

import os
import enum
from typing import Type
from abc import abstractmethod

from tp.libs.python.decorators import classproperty

from .base import AFnBase


class AFnApp(AFnBase):
    """Overloads `AFnBase` exposing functions to handle application related behaviours."""

    __extensions__: Type[enum.IntEnum] | None = None

    # noinspection PyPep8Naming,PyMethodParameters
    @classproperty
    def FileExtensions(cls) -> Type[enum.IntEnum]:
        """Getter method that returns the file extensions enumerator for this application.

        :return: file extensions enumerator.
        """

        return cls.__extensions__

    @abstractmethod
    def extensions(self) -> tuple[enum.IntEnum]:
        """Returns a list of application file extensions.

        :return: application file extensions.
        """

        pass

    @abstractmethod
    def version(self) -> int | float:
        """Returns the version of the application.

        :return: application version.
        """

        pass

    @abstractmethod
    def version_name(self) -> str:
        """Returns the version name of the application.

        :return: application version name.
        """

        pass

    @abstractmethod
    def is_batch(self) -> bool:
        """Returns whether the application is running in batch mode.

        :return: True if application is running in batch mode; False otherwise.
        """

        pass

    def is_valid_extension(self, path: str) -> bool:
        """Returns whether the given path has a valid extension for the application.

        :param path: path to check.
        :return: True if the path has a valid extension; False otherwise.
        """

        extension = ""
        if path and os.path.isfile(path):
            directory, filename = os.path.split(path)
            name, extension = os.path.splitext(filename)
        else:
            extension = path

        # Compare extension with enumerators
        extensions = [member.name.lower() for member in self.extensions()]
        extension = extension.lstrip(".").lower()

        return extension in extensions
