if exist venv del venv
"C:\Program Files\Python310\Scripts\virtualenv.exe" venv
pushd %CD%
cd venv
cd Scripts
call activate
popd
pip install --no-cache-dir -r requirements_standalone.txt
pause
