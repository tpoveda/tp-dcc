tp-dcc
============================================================

.. image:: https://img.shields.io/badge/Python-3.7-yellow?logo=python
    :target: https://www.python.org/

.. image:: https://img.shields.io/badge/Windows-blue?logo=windows
    :target: https://www.python.org/

.. image:: https://img.shields.io/badge/code_style-pep8-blue
    :target: https://www.python.org/dev/peps/pep-0008/

.. image:: https://img.shields.io/badge/Maya-2022-green?logo=autodesk
    :target: https://www.autodesk.com/

.. image:: https://img.shields.io/badge/Maya-2023-green?logo=autodesk
    :target: https://www.autodesk.com/

============================================================


DCC agnostic framework that allows the creation of tools that can work under any DCC that supports Python. The framework contains tools that can be interesting for all people using a specific DCC: nomenclature manager, renamer, etc.

* Python 2 and 3 support
* Reroute DCC agnostic layer
* Generic DCC objects
* Inheritance based configuration files system. Your tools can use different configurations based on which DCC you are working on.
* Generic DCC agnostic TCP client/server implementation. Launch your tool outisde your DCC.
* Huge collection of Python related utils modules: string management, file IO, etc.
* Huge collection of Qt widgets. Your tools will look similar no matter which DCC are your workign on.
* Complete Qt style/theme manager.
* DCC agnostic Python based unit test framework.
* And much more ...


Packages
============================================================

tp-dcc-bootstrap
-----------------

Handles the initialization of the tpDcc framework and all their packages.

tp-dcc-common
-----------------

Shared common libraries used by tpDcc.

Following libraries are available:

- **python**: Collection of Python utilities modules to work with Python and DCCs.
- **qt**: Collection of Python utilities modules to work with PySide/PyQt and DCCs
- **resources**: Resources used by tpDcc framework. Also contains functionality to load resources for apps.
- **math**: Library that contains math related classes and functions for Python.
- **plugin**: Library that contains classes to implement plugin architecture in Python.
- **composite**: Library that contains classes to implement composite architecture in Python.
- **naming**: Library that allows to manage nomenclature using rules and tokens.
- **svg**: Library to handle SVG files in Python.
- **psd**: Library that contains functions to interact with Photoshop files.
- **unittests**: Library to manage unit tests in a DCC agnostic way.
- **nodegraph**: Library to create node graphs in a DCC agnostic way.

tp-dcc-preferences
-----------------

Hello World

tp-dcc-core
-----------------

* **tp-dcc-core**: Collection of Python modules to interact with DCCs Python APIs in a DCC agnostic way.


Requirements
============================================================

* Make sure **Python 3.X** is installed in your machine.

    .. note::
        Scripts expect to find Python executables in their default locations:
            * **Python 3**: C:\Python3X

        You can edit **setup_venv_py.bat** if you want to use custom Python installation directory.

* Make sure **virtualenv** is installed:

      .. code-block::

            pip install virtualenv


* Make **Git** client is installed : https://git-scm.com/


How to use
============================================================

1. Run **setup_venv_py.bat**: to create virtual environment for Python 3.

2. Execute **tpdcc_main.py** in your favorite Python DCC editor to load tpDcc framework.