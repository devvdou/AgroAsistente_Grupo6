# AgroAsistente Chile

Aplicación académica Django para pequeños productores de Chile. Implementa HU-01 a HU-09 con Firebase Realtime Database, Gemini mediante `google-genai`, respaldo local y Open-Meteo. HU-10 a HU-12 están fuera del alcance.

## Requisitos

- Windows con Python 3.11 o 3.12.
- Proyecto Firebase con Realtime Database y cuenta de servicio nueva.
- Clave de Gemini habilitada para `gemini-3.5-flash-lite`.

## Instalación exacta en Windows

1. Ejecute `INSTALAR_WINDOWS.bat`.
2. Edite `.env` y configure `FIREBASE_DATABASE_URL` y `GEMINI_API_KEY`.
3. Copie la cuenta de servicio como `credentials\firebase-admin.json`.
4. Ejecute `COMPROBAR_WINDOWS.bat`.
5. Ejecute `INICIAR_WINDOWS.bat` y abra `http://127.0.0.1:8000/`.

El instalador valida Python, crea `.venv`, instala `requirements.txt`, crea `.env` solo si falta, genera un `DJANGO_SECRET_KEY` aleatorio cuando conserva el ejemplo y crea `credentials`. No imprime secretos.

`COMPROBAR_WINDOWS.bat` rechaza entornos ausentes, valores de ejemplo y credenciales inválidas antes de ejecutar `manage.py check` y las 59 pruebas. `INICIAR_WINDOWS.bat` hace la misma comprobación antes del servidor.

## Configuración

`.env.example` contiene `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `FIREBASE_DATABASE_URL`, `FIREBASE_CREDENTIALS_PATH`, `GEMINI_API_KEY`, `GEMINI_MODEL` y `AI_DAILY_LIMIT`.

La ruta Firebase se resuelve desde `BASE_DIR`. `.env` y todos los JSON de `credentials/` están ignorados. Cada compañero debe crear sus propias credenciales; no debe copiar las de la demostración.

También existe un asistente opcional para Git Bash:

```bash
bash scripts/configurar_credenciales.sh
```

## Funcionamiento

- `/`: contexto de región, predio, modo, cultivo y superficie.
- `/consulta/`: Gemini o respaldo local, más pronóstico.
- `/labores/`: crear, listar y cambiar estado.
- `/estimacion/`: superficie × dosis técnica declarada.

La cuota global usa fecha de Chile, ID por intento, transacciones Firebase y contadores de intentos, respuestas exitosas, fallidas, bloqueadas y excesos. Gemini tiene timeout de 25 segundos y un reintento únicamente para timeout, 429 o 5xx.

## Pruebas

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Las pruebas automáticas no consumen servicios externos. La verificación real de Firebase, Gemini, Open-Meteo y navegador está en `docs/PRUEBAS_Y_QA.md`.

## Seguridad y límites

No hay autenticación; una cookie firmada mantiene el contexto. El límite de IA es global. No se guarda historial de preguntas. Las respuestas son orientación general y no sustituyen a profesionales. En producción se requieren HTTPS y `DJANGO_DEBUG=False`.

Si Gemini falla se muestra “Orientación local de respaldo”. Si Open-Meteo falla, consulta, labores y estimación siguen disponibles.

