# Guion de demostración — cinco minutos

## 0:00–1:00 · Sprint 1

Configurar Maule, predio, Tomate y 500 m². Enviar una pregunta de riego. Mostrar “Respuesta generada por Gemini”, contexto y validación.

## 1:00–2:00 · Sprint 2

Crear una labor, cambiarla a Hecha y abrir Estimación. Ingresar una dosis ficticia declarada; explicar superficie × dosis y que la aplicación no prescribe dosis.

## 2:00–3:30 · Sprint 3

Mostrar pronóstico de Talca con Open-Meteo. Preguntar por una vaca enferma y destacar la negativa de medicamentos. Explicar intentos, éxitos, fallos y bloqueos.

## 3:30–4:30 · Sprint 4

Ejecutar `COMPROBAR_WINDOWS.bat`, mostrar 65 pruebas y el diseño móvil. Señalar `.env.example`, `credentials/README.txt` y el repositorio sin secretos. Editar la superficie y comprobar que las labores continúan visibles.

## 4:30–5:00 · Alternativa

Si Gemini falla, mostrar “Orientación local de respaldo”. Si Open-Meteo falla, señalar su mensaje y continuar. Nunca abrir claves durante la presentación.

Sin internet, la estimación funciona localmente y la consulta usa el respaldo contextual si la cuota no puede verificarse. La persistencia y listado de labores requieren Firebase; no se debe presentarlos como disponibles sin conexión. Conservar las capturas y la evidencia de QA para explicar el recorrido real ya comprobado. Instalar las dependencias antes de llegar al laboratorio.

Antes de presentar: comprobar configuración con el BAT, revisar intentos disponibles, abrir el navegador y probar edición de contexto, estado de labor y fórmula con datos ficticios. Reservar las consultas reales de Gemini para la demostración. Después: retirar archivos privados del computador compartido y revocar las credenciales temporales.
