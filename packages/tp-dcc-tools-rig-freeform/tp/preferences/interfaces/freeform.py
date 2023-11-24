from tp.preferences import manager


def freeform_interface():
    """
    Returns the Freeform preference interface.

    :return: Freeform preference interface instance.
    :rtype: FreeformPreferenceInterface
    """

    return manager.preference().interface('freeform')
