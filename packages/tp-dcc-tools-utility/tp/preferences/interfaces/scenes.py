from tp.preferences import manager


def maya_scenes_interface():
    """
    Returns the scenes preferences instance.
    """

    return manager.preference().interface('maya_scenes_interface')
