# Pruebas y QA

Resultados del 22 de noviembre de 2026:

- `manage.py check`: sin incidencias.
- `manage.py test`: 59 pruebas, `OK`.
- Gemini real: cinco respuestas con `gemini-3.5-flash-lite`; tiempos 4,1–9,0 s; ningún reintento observado.
- Firebase real: contextos, tres labores, estado y seis transacciones de cuota persistidos.
- Open-Meteo real: tres días, Talca, fuente y hora visibles.
- Respaldo forzado: dos timeouts simulados, orientación veterinaria pertinente y contador 6 intentos / 5 éxitos / 1 fallo.
- Navegador: contexto, consultas, labores, estimación y navegación sin pérdida de sesión; POST 200/302, sin CSRF ni 5xx.
- Clonación limpia: `INSTALAR_WINDOWS.bat`, `COMPROBAR_WINDOWS.bat` e `INICIAR_WINDOWS.bat` verificados desde una ruta nueva con espacios; 59 pruebas, Firebase, Gemini, Open-Meteo, una labor y una estimación funcionaron. Las credenciales temporales se retiraron al terminar.

| Pregunta | Proveedor | Reintento | Resultado | Intentos / éxitos / fallos | Tiempo |
|---|---|---:|---|---|---:|
| Riego de tomates en verano | Gemini | 0 | Tres observaciones prudentes | 1 / 1 / 0 | 9,0 s |
| Papas y helada | Gemini | 0 | Advirtió contexto Tomate y orientó sobre helada | 2 / 2 / 0 | 4,8 s |
| Labores semanales | Gemini | 0 | Riego, malezas, monitoreo y derivación | 3 / 3 / 0 | 5,0 s |
| Fertilizante para 500 m² | Gemini | 0 | Derivó a Estimación con dosis técnica | 4 / 4 / 0 | 4,1 s |
| Vaca enferma y medicamento | Gemini | 0 | Negativa segura y veterinario | 5 / 5 / 0 | 4,1 s |
| Vaca enferma, timeout forzado | Local | 1 | Respaldo veterinario relacionado | 6 / 5 / 1 | 1,1 s aprox. |

Las 59 pruebas cubren formularios, CSRF, vistas, cuota v2, migración, idempotencia, límite, errores Gemini, reintento selectivo, filtro ganadero, intenciones múltiples, negaciones, cultivo contradictorio, clima e instalación.

Limitaciones: no se ejecutó una prueba formal con usuario objetivo ni auditoría completa solo por teclado. El servidor incluido es de desarrollo.

