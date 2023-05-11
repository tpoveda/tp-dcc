if exist venv310 del venv310
"C:\Program Files\Python310\Scripts\virtualenv.exe" venv310
pushd %CD%
cd venv310
cd Scripts
call activate
popd
pip install --no-cache-dir -r requirements.txt
pause
