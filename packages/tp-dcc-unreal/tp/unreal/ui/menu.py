import unreal


def check_menu_exists(menu_path: str) -> bool:
    """
    Returns whether menu with given name exists.

    :param str menu_path: path of the menu.
    :return: True if menu with given path exists; False otherwise.
    :rtype: bool
    """

    return True if unreal.ToolMenus.get().find_menu(menu_path) else False
