from tp.preferences import manager


def frag_interface():
    """
    Returns the FRAG preference interface.

    :return: FRAG preference interface instance.
    :rtype: FragPreferenceInterface
    """

    return manager.preference().interface('frag')
