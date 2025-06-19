from __future__ import annotations

from typing import cast
from collections.abc import Iterator

from tp.libs.maya.om import attributetypes

from .layer import MetaLayer
from .module import MetaModule
from ..base import constants


class MetaModulesLayer(MetaLayer):
    """Extends the `MetaLayer` class to handle operations related to
    meta-modules in a `MetaRig`.

    Attributes:
        ID: A constant identifier representing the type of this meta-layer,
            defined in `constants.MODULES_LAYER_TYPE`.
    """

    ID = constants.MODULES_LAYER_TYPE

    def meta_attributes(self) -> list[dict]:
        """Return the list of default metanode attributes that should be added
        into the metanode instance during creation.

        Returns:
            List of dictionaries with attribute data.
        """

        attrs = super().meta_attributes()

        attrs.extend(
            [
                {
                    "name": constants.MODULES_LAYER_MODULE_GROUPS_ATTR,
                    "isArray": True,
                    "locked": False,
                    "type": attributetypes.kMFnDataString,
                    "children": [
                        {
                            "name": constants.MODULES_LAYER_MODULE_GROUP_NAME_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.MODULES_LAYER_GROUP_MODULES_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                    ],
                },
            ]
        )

        return attrs

    def iterate_modules(self, depth_limit: int = 256) -> Iterator[MetaModule]:
        """Iterate over the meta-modules and yields them one by one if they
        have the specified attribute related to a module type.

        This function goes through the meta-level children up to a given
        recursion depth and filters out only those with a specific attribute.

        Args:
            depth_limit: The maximum depth to recurse into the meta-child
                hierarchy. Defaults to 256.

        Yields:
            A generator yielding the meta-modules possessing the required
                attribute indicating a component type.
        """

        for meta_child in self.iterate_meta_children(depth_limit):
            if meta_child.hasAttribute(constants.MODULE_TYPE_ATTR):
                yield cast(MetaModule, meta_child)

    def modules(self, depth_limit: int = 256) -> list[MetaModule]:
        """Return a list of MetaModule objects by iterating through modules
        up to a specific depth limit.

        Args:
            depth_limit: The maximum depth to iterate through modules. Defaults
                to 256.

        Returns:
            A list of `MetaModule` objects gathered during iteration.
        """

        return list(self.iterate_modules(depth_limit=depth_limit))
