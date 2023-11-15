from tp.preferences import manager


def core_preference_interface():

    """
    Returns the core tpDcc Tools framework preference interface.

    :return: core preference interface instance.
    :rtype: CorePreferenceInterface
    """

    return manager.preference().interface('core')


def theme_preference_interface():
    """
    Returns the core tpDcc Tools framework preference interface.

    :return: core preference interface instance.
    :rtype: ThemePreferenceInterface
    """

    return manager.preference().interface('theme')
