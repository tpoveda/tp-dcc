from __future__ import annotations

import typing
from typing import cast, Any
from collections.abc import Generator

from tp.libs.maya.om import attributetypes

from .abstract_layer import LayerDescriptor
from ..utils import traverse_descriptor_layer_dag
from ..attributes import AttributeDescriptor, attribute_class_for_descriptor
from ...base import constants

if typing.TYPE_CHECKING:
    from ..nodes import GuideDescriptor


class GuideLayerDescriptor(LayerDescriptor):
    """Class that defines a guide layer descriptor."""

    @classmethod
    def from_data(cls, layer_data: dict[str, Any]) -> LayerDescriptor:
        """Creates a layer descriptor instance from a data dictionary.

        Args:
            layer_data: Dictionary containing the layer data.

        Returns:
            The created layer descriptor instance.
        """

        data = {
            constants.DAG_DESCRIPTOR_KEY: layer_data.get(
                constants.DG_DESCRIPTOR_KEY, []
            ),
            constants.DG_DESCRIPTOR_KEY: layer_data.get(
                constants.DG_DESCRIPTOR_KEY, []
            ),
            constants.SETTINGS_DESCRIPTOR_KEY: cls.merge_default_settings(
                layer_data.get(constants.SETTINGS_DESCRIPTOR_KEY, [])
            ),
            constants.METADATA_DESCRIPTOR_KEY: cls.merge_default_metadata(
                layer_data.get(constants.METADATA_DESCRIPTOR_KEY, [])
            ),
        }

        return cls(data)

    # noinspection PyMethodOverriding
    def update(self, kwargs: dict[str, Any]) -> None:
        """Update the layer descriptor with new values.

        Args:
            kwargs: Dictionary containing the new values to update.
        """

        # Update settings.
        settings: list[AttributeDescriptor] = self.get(
            constants.SETTINGS_DESCRIPTOR_KEY, []
        )
        consolidated_settings = {i.name: i for i in settings}
        for i in kwargs.get(constants.SETTINGS_DESCRIPTOR_KEY, []):
            existing = consolidated_settings.get(i["name"])
            if existing is not None and i.get("value") is not None:
                existing.value = i["value"]
            else:
                consolidated_settings[i["name"]] = attribute_class_for_descriptor(i)
        self[constants.SETTINGS_DESCRIPTOR_KEY] = list(consolidated_settings.values())

        # Update metadata.
        self[constants.METADATA_DESCRIPTOR_KEY] = [
            attribute_class_for_descriptor(s)
            for s in kwargs.get(constants.METADATA_DESCRIPTOR_KEY, [])
        ] or self.get(constants.METADATA_DESCRIPTOR_KEY, [])

        # Update guides.
        current_guides = {
            g.id: g
            for g in cast(
                list[GuideDescriptor], self.get(constants.DAG_DESCRIPTOR_KEY, [])
            )
        }
        new_or_updated_guide_ids: list[str] = []
        for dag_node in traverse_descriptor_layer_dag(kwargs):
            new_or_updated_guide_ids.append(dag_node.id)
            current_node = self.guide(dag_node.id)
            if current_node is not None:
                current_node.pivotColor = current_node.pivotColor
                current_node.update(**dag_node.to_dict())
            else:
                self.create_guide(**dag_node.to_dict())
        to_purge = [
            i
            for i, g in current_guides.items()
            if i not in new_or_updated_guide_ids and not g.internal
        ]
        if to_purge:
            self.delete_guides(*to_purge)

        # Update DG graphs.
        dg_graphs = kwargs.get(constants.DG_DESCRIPTOR_KEY, [])
        if dg_graphs is not None:
            self[constants.DG_DESCRIPTOR_KEY] = dg_graphs

        # if constants.SETTINGS_DESCRIPTOR_KEY in kwargs:
        #     kwargs[constants.SETTINGS_DESCRIPTOR_KEY] = self.merge_default_settings(
        #         kwargs[constants.SETTINGS_DESCRIPTOR_KEY]
        #     )
        # if constants.METADATA_DESCRIPTOR_KEY in kwargs:
        #     kwargs[constants.METADATA_DESCRIPTOR_KEY] = self.merge_default_metadata(
        #         kwargs[constants.METADATA_DESCRIPTOR_KEY]
        #     )

        super().update(kwargs)

    # === region Settings === #

    @classmethod
    def default_guide_settings(cls) -> list[AttributeDescriptor]:
        """Return the default guide settings for attributes.

        This class method generates a list of attribute descriptors
        representing default settings for a guide configuration.

        Returns:
            A list containing the default attribute descriptors for the guide
            configuration.
        """

        return [
            attribute_class_for_descriptor(d)
            for d in [
                {
                    "name": constants.GUIDE_MANUAL_ORIENT_DESCRIPTOR_KEY,
                    "type": attributetypes.kMFnNumericBoolean,
                    "value": False,
                    "default": False,
                    "channelBox": True,
                    "keyable": False,
                }
            ]
        ]

    @classmethod
    def merge_default_settings(
        cls, settings: list[AttributeDescriptor]
    ) -> list[AttributeDescriptor]:
        """Merge a provided list of settings with the default guide settings
        of the class, ensuring  that each setting in the input settings
        either updates an existing default setting or is added as a new
        default setting.

        Args:
            settings: A list of settings represented as dictionaries,
                where each dictionary contains the name and value of a setting.

        Returns:
            A list of attribute descriptors that represent the merged settings,
            including both the default settings and any updated or added
            settings from the input.
        """

        default_settings = {i.name: i for i in cls.default_guide_settings()}
        for setting in settings:
            existing_attr = default_settings.get(setting.name)
            if existing_attr is not None:
                existing_attr.value = setting.value
            else:
                default_settings[setting.name] = setting

        return list(default_settings.values())

    # endregion

    # === region Metadata === #

    @classmethod
    def default_metadata_settings(cls) -> list[AttributeDescriptor]:
        """Return the default metadata settings for attributes.

        This class method generates a list of attribute descriptors
        representing default metadata settings.

        Returns:
            A list containing the default attribute descriptors for metadata.
        """

        return [
            attribute_class_for_descriptor(d)
            for d in [
                {
                    "name": constants.GUIDES_LAYER_GUIDE_VISIBILITY_ATTR,
                    "type": attributetypes.kMFnNumericBoolean,
                    "value": True,
                    "default": True,
                },
                {
                    "name": constants.GUIDE_LAYER_GUIDE_CONTROL_VISIBILITY_DESCRIPTOR_KEY,
                    "type": attributetypes.kMFnNumericBoolean,
                    "value": False,
                    "default": False,
                },
                {
                    "name": constants.GUIDE_LAYER_PIN_SETTINGS_DESCRIPTOR_KEY,
                    "children": [
                        {
                            "name": constants.GUIDE_LAYER_PINNED_DESCRIPTOR_KEY,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                        {
                            "name": constants.GUIDE_LAYER_PINNED_CONSTRAINTS_DESCRIPTOR_KEY,
                            "type": attributetypes.kMFnDataString,
                        },
                    ],
                },
            ]
        ]

    @classmethod
    def merge_default_metadata(
        cls, metadata: list[AttributeDescriptor]
    ) -> list[AttributeDescriptor]:
        """Merge a provided list of metadata with the default metadata
        of the class, ensuring that each metadata entry in the input
        either updates an existing default metadata entry or is added
        as a new default metadata entry.

        Args:
            metadata: A list of metadata entries represented as dictionaries,
                where each dictionary contains the name and value of a metadata entry.

        Returns:
            A list of dictionaries that represent the merged metadata,
            including both the default metadata and any updated or added
            metadata entries from the input.
        """

        default_metadata = {i.name: i for i in cls.default_metadata_settings()}
        for data in metadata:
            if not data:
                continue
            default_metadata[data.name] = data

        return list(default_metadata.values())

    # endregion

    # === Guides === #

    def has_guides(self) -> bool:
        """Check if the layer has guides.

        Returns:
            True if the layer has guides, False otherwise.
        """

        return bool(self.get(constants.DAG_DESCRIPTOR_KEY, []))

    def iterate_guides(self, include_root: bool) -> Generator[GuideDescriptor]:
        guide_descriptors: list[GuideDescriptor] = self.get(
            constants.DAG_DESCRIPTOR_KEY, []
        )
        for guide_descriptor in iter(guide_descriptors):
            if not include_root and guide_descriptor.id == "root":
                for child in guide_descriptor.iterate_children():
                    yield cast(GuideDescriptor, child)
            else:
                yield guide_descriptor
                for child in guide_descriptor.iterate_children():
                    yield cast(GuideDescriptor, child)

    def guides(self, include_root: bool = True) -> list[GuideDescriptor]:
        """Return the list of guides in the layer.

        Args:
            include_root: Whether to include the root guide in the count.
                Default is True.

        Returns:
            The list of guides in the layer.
        """

        return list(self.iterate_guides(include_root=include_root))

    def guide_count(self, include_root: bool = True) -> int:
        """Return the number of guides in the layer.

        Args:
            include_root: Whether to include the root guide in the count.
                Default is True.

        Returns:
            The number of guides in the layer.
        """

        return len(self.guides(include_root=include_root))

    def guide(self, guide_id) -> GuideDescriptor | None:
        """Return the guide with the given ID.

        Args:
            guide_id: The ID of the guide to return.

        Returns:
            The guide with the given ID, or None if not found.
        """

        return self.node(guide_id)

    def find_guides(self, *guide_ids: str) -> list[GuideDescriptor]:
        """Find and return a list of guides matching the provided IDs.

        Args:
            *guide_ids: Variable length argument list of guide IDs to search for.

        Returns:
            A list of GuideDescriptor instances that match the provided IDs.
            If no matches are found, an empty list is returned.
        """

        return self.find_nodes(*guide_ids)

    # endregion
