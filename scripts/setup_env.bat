@echo off
setlocal enabledelayedexpansion

set "PYTHON37_PATH=C:\Program Files\Python37\python.exe"
set "PYTHON39_PATH=C:\Program Files\Python39\python.exe"
set "PYTHON310_PATH=C:\Program Files\Python310\python.exe"


rem Define the supported Python versions environment variables
set "PYTHON_VERSIONS=PYTHON37_PATH PYTHON39_PATH PYTHON310_PATH"

rem Set the path to the setup_env.py script
set "SCRIPT_PATH=setup_env.py"

rem Set the directory for the virtual environments
set "ROOT_VENV_DIR=..\venvs\venv"

rem Loop through each Python version
for %%v in (%PYTHON_VERSIONS%) do (
    set "PYTHON_EXECUTABLE=!%%v!"
    set "PYTHON_VERSION=!PYTHON_EXECUTABLE:~23,-11!"
    set "VENV_DIR=!ROOT_VENV_DIR!!PYTHON_VERSION!"
    if exist "!PYTHON_EXECUTABLE!" (
        echo Creating virtual environment for Python version !PYTHON_VERSION! in !VENV_DIR!...
        "!PYTHON_EXECUTABLE!" "%SCRIPT_PATH%" --venv-dir "!VENV_DIR!"
        echo.
    ) else (
        echo Python version !PYTHON_VERSION! is not installed. Skipping.
        echo.
    )
)

echo Setup completed successfully.

endlocal