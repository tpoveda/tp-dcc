@echo off

REM The Python virtual environment cannot be called directly from mayapy.
REM Instead a soft link needs to be made to mayapy from a command called "python" within the same directory,
REM and venv needs to be called from this python command.
REM "https://help.autodesk.com/view/MAYACRE/ENU/?guid=GUID-6AF99E9C-1473-481E-A144-357577A53717"

REM Set the path to Maya's Python interpreter
set MAYAPY_PATH="C:\Program Files\Autodesk\Maya2025\bin\python.exe"

REM Get the directory where the batch file is located
set BATCH_DIR=%~dp0

REM Set the directory for the virtual environment
set VENV_DIR="%BATCH_DIR%venvs\maya2025"

REM Create the virtual environment
%MAYAPY_PATH% -m venv %VENV_DIR%

REM Activate the virtual environment
call %VENV_DIR%\Scripts\activate.bat

REM Install the packages from requirements.txt if it exists
if exist "%BATCH_DIR%requirements.txt" (
    pip install -r "%BATCH_DIR%requirements.txt"
    echo Installed packages from requirements.txt
) else (
    echo No requirements.txt found. Skipping package installation.
)

REM Install the packages from requirements-dev.txt if it exists
if exist "%BATCH_DIR%requirements-dev.txt" (
    pip install -r "%BATCH_DIR%requirements-dev.txt"
    echo Installed packages from requirements-dev.txt
) else (
    echo No requirements-dev.txt found. Skipping package installation.
)