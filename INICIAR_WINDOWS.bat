@echo off
setlocal
pushd "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Falta el entorno virtual. Ejecute primero INSTALAR_WINDOWS.bat.
    goto :error
)
if not exist ".env" (
    echo Falta .env. Ejecute INSTALAR_WINDOWS.bat y complete la configuracion.
    goto :error
)
if not exist "credentials\firebase-admin.json" (
    echo Falta credentials\firebase-admin.json.
    echo Copie en esa ruta una cuenta de servicio nueva de Firebase.
    goto :error
)

call ".venv\Scripts\activate.bat" || goto :error
python scripts\configuracion_local.py || goto :error
echo La aplicacion estara disponible en http://127.0.0.1:8000/
python -u manage.py runserver 127.0.0.1:8000 --noreload
set "SERVER_EXIT=%ERRORLEVEL%"
popd
exit /b %SERVER_EXIT%

:error
pause
popd
exit /b 1
