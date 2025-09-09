from __future__ import annotations

from tp.libs.maya.om import attributetypes

from ..layer import MetaLayer
from ...base import constants


class MetaGuidesLayer(MetaLayer):
    ID = constants.GUIDE_LAYER_TYPE

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
                    "name": constants.GUIDES_LAYER_GUIDES_ATTR,
                    "isArray": True,
                    "locked": False,
                    "children": [
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_ID_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                        {
                            "name": constants.GUIDES_LAYER_SRTS_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                            "isArray": True,
                        },
                        {
                            "name": constants.GUIDES_LAYER_SHAPE_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                        {
                            "name": constants.GUIDES_LAYER_SOURCE_GUIDES_ATTR,
                            "type": attributetypes.kMFnCompoundAttribute,
                            "isArray": True,
                            "children": [
                                {
                                    "name": constants.GUIDES_LAYER_SOURCE_GUIDE_ATTR,
                                    "type": attributetypes.kMFnMessageAttribute,
                                },
                                {
                                    "name": constants.GUIDES_LAYER_CONSTRAINT_NODES_ATTR,
                                    "type": attributetypes.kMFnMessageAttribute,
                                    "isArray": True,
                                },
                            ],
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_MIRROR_ROTATION_ATTR,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_AUTO_ALIGN_ATTR,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_AIM_VECTOR_ATTR,
                            "type": attributetypes.kMFnNumeric3Float,
                        },
                        {
                            "name": constants.GUIDES_LAYER_GUIDE_UP_VECTOR_ATTR,
                            "type": attributetypes.kMFnNumeric3Float,
                        },
                    ],
                },
                {
                    "name": constants.GUIDES_LAYER_GUIDE_VISIBILITY_ATTR,
                    "type": attributetypes.kMFnNumericBoolean,
                    "default": True,
                    "value": True,
                },
                {
                    "name": constants.GUIDES_LAYER_GUIDE_CONTROL_VISIBILITY_ATTR,
                    "type": attributetypes.kMFnNumericBoolean,
                    "default": False,
                    "value": False,
                },
                {
                    "name": constants.GUIDES_LAYER_PIN_SETTINGS_ATTR,
                    "children": [
                        {
                            "name": constants.GUIDES_LAYER_PINNED_ATTR,
                            "type": attributetypes.kMFnNumericBoolean,
                        },
                        {
                            "name": constants.GUIDES_LAYER_PINNED_CONSTRAINTS_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                    ],
                },
                {
                    "name": constants.GUIDES_LAYER_LIVE_LINK_NODES_ATTR,
                    "type": attributetypes.kMFnMessageAttribute,
                    "isArray": True,
                },
                {
                    "name": constants.GUIDES_LAYER_LIVE_LINK_IS_ACTIVE_ATTR,
                    "type": attributetypes.kMFnNumericBoolean,
                    "value": False,
                    "default": False,
                },
                {
                    "name": constants.GUIDES_LAYER_CONNECTOR_GROUP_ATTR,
                    "type": attributetypes.kMFnMessageAttribute,
                },
                {
                    "name": constants.GUIDES_LAYER_DG_GRAPH_ATTR,
                    "isArray": True,
                    "children": [
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_ID_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_NODES_ATTR,
                            "type": attributetypes.kMFnCompoundAttribute,
                            "isArray": True,
                            "children": [
                                {
                                    "name": constants.GUIDES_LAYER_DG_GRAPH_NODE_ID_ATTR,
                                    "type": attributetypes.kMFnDataString,
                                },
                                {
                                    "name": constants.GUIDES_LAYER_DG_GRAPH_NODE_ATTR,
                                    "type": attributetypes.kMFnMessageAttribute,
                                },
                            ],
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_NAME_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_METADATA_ATTR,
                            "type": attributetypes.kMFnDataString,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_INPUT_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                        {
                            "name": constants.GUIDES_LAYER_DG_GRAPH_OUTPUT_NODE_ATTR,
                            "type": attributetypes.kMFnMessageAttribute,
                        },
                    ],
                },
            ]
        )

        return attrs
