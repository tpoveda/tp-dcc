if exist venv39 del venv39
"C:\Program Files\Python39\Scripts\virtualenv.exe" venv39
pushd %CD%
cd venv39
cd Scripts
call activate
popd
pip install --no-cache-dir -r requirements.txt
pause
