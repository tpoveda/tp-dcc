```bat
@echo off
setlocal

echo [*] Generating API docs from tp/...
sphinx-apidoc -o docs/source/api tp --force --no-toc --separate

echo [*] Building documentation...
python -m sphinx -b html docs/ docs/_build/html

echo [✓] Documentation built in: docs/_build/html