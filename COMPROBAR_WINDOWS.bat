@echo off
setlocal
pushd "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Falta el entorno virtual. Ejecute primero INSTALAR_WINDOWS.bat.
    goto :error
)

call ".venv\Scripts\activate.bat" || goto :error
python scripts\configuracion_local.py || goto :error
python manage.py check || goto :error
python manage.py test || goto :error

echo.
echo Comprobacion terminada correctamente.
popd
exit /b 0

:error
echo.
echo La comprobacion encontro un error.
pause
popd
exit /b 1
