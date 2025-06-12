def update_misplaced_members(members):
    """
    Called by Qt.py at run-time to modify the modules it makes available.
    :param dict members: The members considered by Qt.py
    """

    # PySide2
    members["PySide2"]["QtCore.QStandardPaths"] = "QtCore.QStandardPaths"
    members["PySide2"]["QtCore.QMessageLogContext"] = "QtCore.QMessageLogContext"
    members["PySide2"]["QtCore.qInstallMessageHandler"] = (
        "QtCore.qInstallMessageHandler"
    )
    members["PySide2"]["QtCore.QRegularExpression"] = "QtCore.QRegularExpression"
    members["PySide2"]["QtGui.QEnterEvent"] = "QtGui.QEnterEvent"
    members["PySide2"]["QtGui.QExposeEvent"] = "QtGui.QExposeEvent"
    members["PySide2"]["QtGui.QRegularExpressionValidator"] = (
        "QtGui.QRegularExpressionValidator"
    )
    members["PySide2"]["QtGui.QGuiApplication"] = "QtGui.QGuiApplication"
    members["PySide2"]["QtGui.QScreen"] = "QtGui.QScreen"
    members["PySide2"]["QtWidgets.QDesktopWidget"] = "QtWidgets.QDesktopWidget"

    # PySide6
    members["PySide6"]["QtCore.QStandardPaths"] = "QtCore.QStandardPaths"
    members["PySide6"]["QtCore.QMessageLogContext"] = "QtCore.QMessageLogContext"
    members["PySide6"]["QtCore.qInstallMessageHandler"] = (
        "QtCore.qInstallMessageHandler"
    )
    members["PySide6"]["QtCore.QRegularExpression"] = "QtCore.QRegularExpression"
    members["PySide6"]["QtGui.QEnterEvent"] = "QtGui.QEnterEvent"
    members["PySide6"]["QtGui.QExposeEvent"] = "QtGui.QExposeEvent"
    members["PySide6"]["QtGui.QRegularExpressionValidator"] = (
        "QtGui.QRegularExpressionValidator"
    )
    members["PySide6"]["QtGui.QGuiApplication"] = "QtGui.QGuiApplication"
    members["PySide6"]["QtGui.QScreen"] = "QtGui.QScreen"
    members["PySide6"]["QtWidgets.QDesktopWidget"] = "QtWidgets.QDesktopWidget"
