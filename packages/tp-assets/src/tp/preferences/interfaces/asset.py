from __future__ import annotations

from tp.preferences import manager


# noinspection PyUnresolvedReferences
def model_assets_interface() -> "ModelAssetsPreferenceInterface":
    """Return the model assets interface.

    Returns:
        The model assets interface instance.
    """

    return manager.current_instance().interface("model_assets")
