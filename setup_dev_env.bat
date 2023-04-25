if exist venv3 del venv
"C:\Program Files\Python39\Scripts\virtualenv.exe" venv
pushd %CD%
cd venv
cd Scripts
call activate
popd
pip install --no-cache-dir -r requirements.txt
pause
