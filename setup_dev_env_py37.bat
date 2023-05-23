if exist venv37 del venv37
"C:\Program Files\Python37\Scripts\virtualenv.exe" venv37
pushd %CD%
cd venv37
cd Scripts
call activate
popd
pip install --no-cache-dir -r requirements.txt
pause
