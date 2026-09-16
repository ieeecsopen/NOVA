@echo off
setlocal
set "DIR=%~dp0"
set "PYTHONPATH=%DIR%;%PYTHONPATH%"
python -m compiler.nova_compiler.cli %*
