@echo off
setlocal
pushd "%~dp0"

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>&1
    if errorlevel 1 goto :sin_python
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info[:2] in ((3,11),(3,12)) else 1)" || goto :sin_python
if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno virtual...
    %PYTHON_CMD% -m venv .venv || goto :error
)

call ".venv\Scripts\activate.bat" || goto :error
python -c "import sys; sys.exit(0 if sys.version_info[:2] in ((3,11),(3,12)) else 1)" || goto :sin_python
python -m pip install --upgrade pip || goto :error
python -m pip install -r requirements.txt || goto :error

python scripts\configuracion_local.py --preparar || goto :error

echo.
echo Instalacion completada.
echo Edite .env y configure FIREBASE_DATABASE_URL y GEMINI_API_KEY.
echo Copie su JSON privado como credentials\firebase-admin.json.
echo Este instalador no solicita ni muestra secretos.
popd
exit /b 0

:sin_python
echo No se encontro Python. Instale Python 3.11 o 3.12 y vuelva a ejecutar este archivo.
pause
popd
exit /b 1

:error
echo La instalacion no pudo completarse. Revise el mensaje anterior.
pause
popd
exit /b 1
