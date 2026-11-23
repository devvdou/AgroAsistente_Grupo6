"""Preparación y comprobación local sin imprimir valores privados."""
import json
import secrets
import sys
from pathlib import Path
from urllib.parse import urlparse
from dotenv import dotenv_values, set_key

BASE = Path(__file__).resolve().parent.parent


def preparar(base=BASE):
    archivo = base / '.env'
    if not archivo.exists():
        archivo.write_bytes((base / '.env.example').read_bytes())
    datos = dotenv_values(archivo)
    if not datos.get('DJANGO_SECRET_KEY') or datos['DJANGO_SECRET_KEY'] == 'genere-una-clave-larga-y-unica':
        set_key(archivo, 'DJANGO_SECRET_KEY', secrets.token_urlsafe(48))
    (base / 'credentials').mkdir(exist_ok=True)


def comprobar(base=BASE):
    errores = []
    if not (base / '.env').exists():
        return ['Falta .env. Ejecute INSTALAR_WINDOWS.bat.']
    datos = dotenv_values(base / '.env')
    for campo in ('DJANGO_SECRET_KEY', 'GEMINI_API_KEY', 'FIREBASE_DATABASE_URL'):
        valor = datos.get(campo, '')
        if not valor or any(x in valor for x in ('genere-una', 'reemplace-', 'SU-PROYECTO')):
            errores.append(f'Complete {campo} en .env.')
    url = urlparse(datos.get('FIREBASE_DATABASE_URL', ''))
    if url.scheme != 'https' or not url.netloc.endswith(('.firebaseio.com', '.firebasedatabase.app')):
        errores.append('FIREBASE_DATABASE_URL no tiene formato válido.')
    try:
        if int(datos.get('AI_DAILY_LIMIT', '0')) < 1:
            raise ValueError
    except ValueError:
        errores.append('AI_DAILY_LIMIT debe ser un entero positivo.')
    ruta = base / (datos.get('FIREBASE_CREDENTIALS_PATH') or 'credentials/firebase-admin.json')
    try:
        credencial = json.loads(ruta.read_text(encoding='utf-8'))
        if credencial.get('type') != 'service_account' or not all(credencial.get(k) for k in ('private_key', 'client_email', 'project_id')):
            raise ValueError
    except (OSError, ValueError):
        errores.append('Falta una cuenta de servicio válida en credentials/firebase-admin.json.')
    return errores


if __name__ == '__main__':
    if sys.version_info[:2] not in ((3, 11), (3, 12)):
        print('Instale Python 3.11 o 3.12.')
        sys.exit(1)
    if '--preparar' in sys.argv:
        preparar()
        print('Configuración local preparada; el secreto Django no se muestra.')
    pendientes = comprobar()
    for mensaje in pendientes:
        print(mensaje)
    if not pendientes:
        print('Configuración local válida (sin prueba de red).')
    sys.exit(0 if '--preparar' in sys.argv else bool(pendientes))
