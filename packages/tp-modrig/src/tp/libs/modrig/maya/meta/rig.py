from __future__ import annotations

from tp.libs.maya.om import attributetypes
from tp.libs.maya.meta.base import MetaBase

from ..base import constants


class ModRig(MetaBase):
    """Metaclass for a ModRig rig in Maya."""

    ID = constants.RIG_TYPE

    def meta_attributes(self) -> list[dict]:
        """Return the list of default metanode attributes that should be added
        into the metanode instance during creation.

        Returns:
            List of dictionaries with attribute data.
        """

        attrs = super().meta_attributes()

        attrs.extend(
            [
                dict(
                    name=constants.VERSION_INFO_ATTR,
                    type=attributetypes.kMFnDataString,
                ),
                dict(name=constants.NAME_ATTR, type=attributetypes.kMFnDataString),
                dict(name=constants.ID_ATTR, type=attributetypes.kMFnDataString),
            ]
        )

        return attrs
