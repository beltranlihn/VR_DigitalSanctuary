@echo off
rem Soul Charger · abre el editor de la obra (servidor local + navegador). Cerrar esta ventana apaga el editor.
cd /d "%~dp0..\.."
python tools\editor\serve_editor.py --open
pause
