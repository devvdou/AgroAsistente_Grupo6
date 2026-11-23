# Resultado final

Fecha: 22 de noviembre de 2026.

## Resultado técnico

- `manage.py check`: sin incidencias.
- `manage.py test`: 59 pruebas, `OK`.
- `pip check`: dependencias consistentes.
- Firebase: contexto, labores, estado y cuota v2 persistidos.
- Gemini: cinco respuestas reales con `gemini-3.5-flash-lite`.
- Open-Meteo: tres días reales para Talca.
- Respaldo: timeout doble controlado, resultado local pertinente y fallo contabilizado.

| Pregunta | Proveedor | Reintento | Resultado mostrado | Intentos | Exitosas | Fallidas | Tiempo |
|---|---|---:|---|---:|---:|---:|---:|
| Riego de tomates en verano | Gemini | 0 | Respuesta generada por Gemini | 1 | 1 | 0 | 9,0 s |
| Papas y helada | Gemini | 0 | Gemini; advirtió contexto Tomate | 2 | 2 | 0 | 4,8 s |
| Labores semanales | Gemini | 0 | Gemini; labores pertinentes | 3 | 3 | 0 | 5,0 s |
| Fertilizante para 500 m² | Gemini | 0 | Gemini; derivó a Estimación | 4 | 4 | 0 | 4,1 s |
| Vaca enferma y medicamento | Gemini | 0 | Gemini; negativa segura | 5 | 5 | 0 | 4,1 s |
| Vaca enferma con timeout forzado | Local | 1 | Orientación local de respaldo | 6 | 5 | 1 | 1,1 s aprox. |

El recorrido creó tres labores, marcó una Hecha y calculó 10 kg como `500 m² × 0,02 kg/m²`, con una dosis ficticia declarada. No hubo errores 5xx, CSRF ni pérdida de sesión.

## Clonación limpia

Se clonó el commit local en `Prueba Clon Limpio AgroAsistente`, una ruta distinta con espacios. `INSTALAR_WINDOWS.bat` creó un entorno desde cero y un secreto Django nuevo. Tras colocar temporalmente las credenciales privadas, `COMPROBAR_WINDOWS.bat` ejecutó 59 pruebas y `INICIAR_WINDOWS.bat` levantó Django. Desde navegador se verificaron Firebase, una respuesta real de Gemini en 4,6 s, tres días de Open-Meteo, una labor, una estimación de 10 kg y conservación del contexto. Consola: 0 errores. Las credenciales temporales fueron retiradas del clon al finalizar.

## Historias

HU-01 a HU-09: **Completa y verificada**, según la evidencia automática y manual detallada en `MATRIZ_TRAZABILIDAD.md`. HU-10 a HU-12 no se implementaron.

## Causas corregidas

La llamada tenía un timeout de 10 segundos, ningún reintento, errores sin categoría y cuota que confundía respuestas confirmadas con reservas. Además, un fallo de Firebase posterior podía reemplazar una respuesta válida. La versión final usa 25 segundos, un reintento selectivo, categorías seguras de error, IDs idempotentes y contadores separados.

## Riesgos restantes

- Dependencia de conectividad y disponibilidad/cuota externa.
- Cuenta de servicio administrativa; requiere IAM mínimo y rotación.
- Sin cuentas de usuario; el aislamiento depende de cookie firmada.
- Servidor Django de desarrollo para la demostración local.
- No existe prueba formal de usabilidad con un usuario objetivo.
