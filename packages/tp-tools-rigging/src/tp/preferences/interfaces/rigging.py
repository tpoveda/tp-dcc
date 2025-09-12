from tp.preferences import manager


# noinspection PyUnresolvedReferences
def controls_creator_interface() -> "ControlsCreatorInterface":
    """Return the interface to interact with the control creator library
    preferences.

    Returns:
        Controls creator interface instance.
    """

    return manager.current_instance().interface("controls_creator")
