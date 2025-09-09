from __future__ import annotations

from typing import Any

from tp.libs.maya.om import attributetypes
from tp.libs.maya.wrapper import DagNode, Plug

from ..layer import MetaLayer
from ...base import constants


class MetaGeometryLayer(MetaLayer):
    """Extends the `MetaLayer` class to define a geometry layer.

    Attributes:
    ID: A constant identifier representing the type of this meta-layer.
    """

    ID = constants.GEOMETRY_LAYER_TYPE

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
                    "name": constants.GEOMETRY_LAYER_GEOMETRIES_ATTR,
                    "isArray": True,
                    "locked": False,
                    "type": attributetypes.kMFnDataString,
                    "children": [
                        {
                            "name": constants.GEOMETRY_LAYER_GEOMETRY_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                        {
                            "name": constants.GEOMETRY_LAYER_CACHE_GEOMETRY_ATTR,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                    ],
                },
            ]
        )

        return attrs

    def geometry_plugs(self) -> Plug:
        """Returns the plug that contains all geometry nodes in this layer.

        Returns:
            The plug containing all geometry nodes.
        """

        return self.attribute(constants.GEOMETRY_LAYER_GEOMETRIES_ATTR)

    def add_geometry(self, geo_node: DagNode) -> bool:
        """Adds a geometry node to the geometry layer.

        Args:
            geo_node: The geometry node to add.

        Returns:
            True if the geometry was added successfully, False otherwise.
        """

        element = self.geometry_plugs().nextAvailableElementPlug()
        geo_node.message.connect(element)

        return True

    def serializeFromScene(*args, **kwargs) -> dict[str, Any]:
        """Serialize the layer from the scene.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            A dictionary containing the serialized layer data.
        """

        return {constants.GEOMETRY_LAYER_TYPE: {}}
