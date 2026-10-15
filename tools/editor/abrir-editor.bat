@echo off

rem Veation VR Studio · abre el editor de la obra en su propia ventana (servidor local + Edge/Chrome en modo app). Cerrar esta ventana apaga el editor.

cd /d "%~dp0..\.."

python tools\editor\serve_editor.py --app

pause

