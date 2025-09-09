from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .module import Module


class BaseSubsystem:
    """Base class for all subsystems.

    A subsystem is a component of a module that encapsulates specific
    functionality or behavior.
    """

    def __init__(self, module: Module):
        """Initialize the subsystem with its parent module.

        Args:
            module: The parent module to which this subsystem belongs.
        """

        self._module = module
