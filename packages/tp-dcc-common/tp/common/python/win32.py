# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions to work with win32
"""

import sys
from typing import Tuple, List

if 'win' in sys.platform:
    import ctypes
    import ctypes.wintypes
    import winreg
    try:
        import win32gui
        import win32process
    except ImportError:
        pass


GWL_WNDPROC = -4
GWL_HINSTANCE = -6
GWL_HWNDPARENT = -8
GWL_STYLE = -16
GWL_EXSTYLE = -20
GWL_USERDATA = -21
GWL_ID = -12

WS_BORDER = 0x800000
WS_CAPTION = 0xc00000
WS_CHILD = 0x40000000
WS_CHILDWINDOW = 0x40000000
WS_CLIPCHILDREN = 0x2000000
WS_CLIPSIBLINGS = 0x4000000
WS_DISABLED = 0x8000000
WS_DLGFRAME = 0x400000
WS_GROUP = 0x20000
WS_HSCROLL = 0x100000
WS_ICONIC = 0x20000000
WS_MAXIMIZE = 0x1000000
WS_MAXIMIZEBOX = 0x10000
WS_MINIMIZE = 0x20000000
WS_MINIMIZEBOX = 0x20000
WS_OVERLAPPED = 0
WS_OVERLAPPEDWINDOW = 0xcf0000
WS_POPUP = 0x80000000
WS_POPUPWINDOW = 0x80880000
WS_SIZEBOX = 0x40000
WS_SYSMENU = 0x80000
WS_TABSTOP = 0x10000
WS_THICKFRAME = 0x40000
WS_TILED = 0
WS_TILEDWINDOW = 0xcf0000
WS_VISIBLE = 0x10000000
WS_VSCROLL = 0x200000


def to_hwnd(pycobject):
    """
    Convenience method to get a Windows Handle from a PySide WinID.
    Based on http://srinikom.github.io/pyside-bz-archive/523.html

    :param pycobject: A value equivalent to a void* that represents the Windows handle if one exists; None otherwise.
    :return: Window handle.
    """

    if type(pycobject) is int:
        # That specific case happen in maya 2017, here, we already have the hwnd so no further manipulation is needed
        return pycobject
    if sys.version_info[0] == 2:
        ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ctypes.py_object]
        return ctypes.pythonapi.PyCObject_AsVoidPtr(pycobject)
    elif sys.version_info[0] == 3:
        ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
        return ctypes.pythonapi.PyCapsule_GetPointer(pycobject, None)


def set_owner(hwnd, hwnd_owner):
    """
    Changes the owner window of the given window
    :param hwnd:
    :param hwnd_owner:
    """

    _update_window = ctypes.windll.user32.UpdateWindow

    # WIN32 vs WIN64 - from a macro in winuser.h
    if ctypes.sizeof(ctypes.wintypes.HWND) == ctypes.sizeof(ctypes.c_long):
        _LONG = ctypes.wintypes.LONG
        _set_window_long = ctypes.windll.user32.SetWindowLongW
        _set_window_long.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.wintypes.LONG]
        _set_window_long.restype = ctypes.c_void_p
    elif ctypes.sizeof(ctypes.wintypes.HWND) == ctypes.sizeof(ctypes.c_longlong):
        _LONG = ctypes.wintypes.HWND
        _set_window_long = ctypes.windll.user32.SetWindowLongPtrW
        _set_window_long.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.wintypes.HWND]
        _set_window_long.restype = _LONG

    last_error = ctypes.set_last_error(0)
    try:
        result = _set_window_long(ctypes.wintypes.HWND(hwnd), ctypes.c_int(GWL_HWNDPARENT), _LONG(hwnd_owner))
    finally:
        last_error = ctypes.set_last_error(last_error)

    if not result and last_error:
        raise ctypes.WinError(last_error)

    _update_window(hwnd_owner)

    return result


def get_reg_key(registry, key, architecture=None):
    """
    Returns a _winreg hkey if found.

    :param registry: str, registry to look in. HKEY_LOCAL_MACHINE for example
    :param key: str, key to open 'Software/Ubisoft/Test' for example
    :param architecture: variant, int || None, 32 or 64 bit. If None, default system architecture is used
    :return: _winreg handle object
    """

    reg_key = None
    a_reg = winreg.ConnectRegistry(None, getattr(winreg, registry))
    if architecture == 32:
        sam = winreg.KEY_WOW64_32KEY
    elif architecture == 64:
        sam = winreg.KEY_WOW64_64KEY
    else:
        sam = 0
    try:
        reg_key = winreg.OpenKey(a_reg, key, 0, winreg.KEY_READ | sam)
    except WindowsError:
        pass

    return reg_key


def list_reg_keys(registry, key, architecture=None):
    """
    Returns a list of child keys as tuples containing:
        - A string that identifies the value name
        - An object that holds the value data, and whose type depends on the underlying registry type
        - An integer that identifies the type of the value data (see table in docs for _winreg.SetValueEx).

    :param registry: str, registry to look in. HKEY_LOCAL_MACHINE for example
    :param key: str, key to open 'Software/Ubisoft/Test' for example
    :param architecture: variant, int || None, 32 or 64 bit. If None, default system architecture is used
    :return: list<tuple>
    """

    reg_key = get_reg_key(registry=registry, key=key, architecture=architecture)
    ret = list()
    if reg_key:
        i = 0
        while True:
            try:
                ret.append(winreg.EnumKey(reg_key, i))
                i += 1
            except WindowsError:
                break

    return ret


def list_reg_key_values(registry, key, architecture=None):
    """
    Returns a list of child keys and their values as tuples containing:
        - A string that identifies the value name
        - An object that holds the value data, and whose type depends on the underlying registry type
        - An integer that identifies the type of the value data (see table in docs for _winreg.SetValueEx)
    :param registry: str, registry to look in. HKEY_LOCAL_MACHINE for example.

    :param key: str, key to open 'Software/Ubisoft/Test' for example
    :param architecture: variant, int || None, 32 or 64 bit. If None, default system architecture is used
    :return: list<tuple>
    """

    reg_key = get_reg_key(registry=registry, key=key, architecture=architecture)
    ret = list()
    if reg_key:
        sub_keys, value_count, modified = winreg.QueryInfoKey(reg_key)
        for i in range(value_count):
            ret.append(winreg.EnumValue(reg_key, i))

    return ret


def registry_value(registry, key, value_name, architecture=None):
    """
    Retruns the value and type of the given registry key value name
    :param registry: str, registry to look in. HKEY_LOCAL_MACHINE for example
    :param key: str, key to open 'Software/Ubisoft/Test' for example
    :param value_name: str, name of the value to read. To read the 'default' key, pass an empty string
    :param architecture: variant, int || None, 32 or 64 bit. If None, default system architecture is used
    :return: tuple<object, int, value stored in key and registry type for value (see _winreg's Value Types)
    """

    reg_key = get_reg_key(registry, key, architecture=architecture)
    if reg_key:
        value = winreg.QueryValueEx(reg_key, value_name)
        winreg.CloseKey(reg_key)
        return value

    return '', 0


def monitors() -> List:
    """
    Returns a list of all monitors.

    code.activestate.com/recipes/460509-get-the-actual-and-usable-sizes-of-all-the-monitor
    :return: list of active monitors.
    :rtype: List
    """

    result = list()

    CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(Rect), ctypes.c_double)

    def _cb(h_monitor, hdc_monitor, l_prc_monitor, dw_data):
        r = l_prc_monitor.contents
        data = [h_monitor]
        data.append(r.dump())
        result.append(data)

        return 1

    cb_fn = CBFUNC(_cb)
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, cb_fn, 0)

    return result


def active_monitor_areas():
    """
    Returns the active and working area of each monitor.

    code.activestate.com/recipes/460509-get-the-actual-and-usable-sizes-of-all-the-monitor
    :return:
    """

    result = list()
    for h_monitor, extents in monitors():
        data = [h_monitor]
        monitor_info = MonitorInfo()
        monitor_info.cbSize = ctypes.sizeof(MonitorInfo)
        monitor_info.rcMonitor = Rect()
        monitor_info.rcWork = Rect()
        ctypes.windll.user32.GetMonitorInfoA(h_monitor, ctypes.byref(monitor_info))
        data.append(monitor_info.rcMonitor.dump())
        data.append(monitor_info.rcWork.dump())
        result.append(data)

    return result


def set_coordinates_to_screen(x: int, y: int, w: int, h: int, padding: int = 0) -> Tuple[int, int]:
    """
    With the given window position and size, finds a location where the window is not off-screen.

    :param int x: X position of the window.
    :param int y: Y position of the window.
    :param int w: width of the window.
    :param int h: height of the windowd.
    :param padding: optional extra padding.
    :return: tuple containing a valid window position.
    :rtype: Tuple[int, int]
    """

    monitor_adjusted = [
        (x1, y1, x2 - w - padding, y2 - h - padding) for x1, y1, x2, y2 in tuple(m[1] for m in active_monitor_areas())]
    location_groups = tuple(zip(*monitor_adjusted))

    x_orig = x
    y_orig = y
    if monitor_adjusted:
        # Make sure window is within monitor bounds
        x_min = min(location_groups[0])
        x_max = max(location_groups[2])
        y_min = min(location_groups[1])
        y_max = max(location_groups[3])

        if x < x_min:
            x = x_min
        elif x > x_max:
            x = x_max
        if y < y_min:
            y = y_min
        elif y > y_max:
            y = y_max

        # Check offset to find the closest monitor
        monitor_offsets = dict()
        for monitor_location in monitor_adjusted:
            monitor_offsets[monitor_location] = 0
            x1, y1, x2, y2 = monitor_location
            if x < x1:
                monitor_offsets[monitor_location] += x1 - x
            elif x > x2:
                monitor_offsets[monitor_location] += x - x2
            if y < y1:
                monitor_offsets[monitor_location] += y1 - y
            elif y > y2:
                monitor_offsets[monitor_location] += y - y2

        # Check the window is correctly in the monitor
        x1, y1, x2, y2 = min(monitor_offsets.items(), key=lambda d: d[1])[0]
        if x < x1:
            x = x1
        elif x > x2:
            x = x2
        if y < y1:
            y = y1
        elif y > y2:
            y = y2

    # Reverse window padding if needed
    if x != x_orig:
        x -= padding
    if y != y_orig:
        y -= padding

    return x, y


def focus_window_from_pid(window_pid, restore=True):

    def _window_enumeration_handler(hwnd, list_to_append):
        list_to_append.append((hwnd, win32gui.GetWindowText(hwnd)))

    hwnds = get_hwnds_for_pid(window_pid)

    window_list = []
    win32gui.EnumWindows(_window_enumeration_handler, window_list)
    for i in window_list:
        if i[0] in hwnds:
            show_type = 9 if restore else 5
            win32gui.ShowWindow(i[0], show_type)
            win32gui.SetForegroundWindow(i[0])
            break


def get_hwnds_for_pid(pid):

    def _window_enumeration_handler(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(_window_enumeration_handler, hwnds)
    return hwnds


def _get_win_folder_from_registry(csidl_name):
    """
    Based on appdirs _get_win_folder_from_registry function
    """

    shell_folder_name = {
        "CSIDL_APPDATA": "AppData",
        "CSIDL_COMMON_APPDATA": "Common AppData",
        "CSIDL_LOCAL_APPDATA": "Local AppData",
    }[csidl_name]

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    )
    dir, type = winreg.QueryValueEx(key, shell_folder_name)

    return dir


def _get_win_folder_with_ctypes(csidl_name):
    """
    Based on appdirs _get_win_folder_with_ctypes function
    """

    csidl_const = {
        "CSIDL_APPDATA": 26,
        "CSIDL_COMMON_APPDATA": 35,
        "CSIDL_LOCAL_APPDATA": 28,
    }[csidl_name]

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

    # Downgrade to short path name if it has highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = False
    for c in buf:
        if ord(c) > 255:
            has_high_char = True
            break
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    return buf.value


if 'win' in sys.platform:
    try:
        get_win_folder = _get_win_folder_with_ctypes
    except ImportError:
        get_win_folder = _get_win_folder_from_registry

    class Rect(ctypes.Structure):
        _fields_ = [
            ('left', ctypes.c_long),
            ('top', ctypes.c_long),
            ('right', ctypes.c_long),
            ('bottom', ctypes.c_long)
        ]

        def dump(self):
            return tuple(map(int, (self.left, self.top, self.right, self.bottom)))

    class MonitorInfo(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_long),
            ('rcMonitor', Rect),
            ('rcWork', Rect),
            ('dwFlags', ctypes.c_long)
        ]
