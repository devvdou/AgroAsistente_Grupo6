# Pruebas y QA

## Fase A — 24 de noviembre de 2026

Estado: Fase A aceptada por el usuario el 24 de noviembre de 2026. Confirmó ID estable, labor visible y modificable a Hecha tras recargar, y respuesta correcta de Gemini. Autorizó la Fase B de empaquetado. No se creó ZIP ni commit ni publicación durante la Fase A. Los resultados del 22 de noviembre conservados más abajo son históricos.

Fase B: suite repetida antes del commit, 65 pruebas OK, check y pip check sin incidencias. Para conservar la cuota de demostración no se requieren nuevas consultas reales de Gemini: se mantienen las verificaciones reales de Fase A y del usuario. La comprobación del commit empaquetado se ejecuta desde un clon nuevo con los tres BAT; su hash y resultado se informan junto con el ZIP, evitando incluir en el commit un hash de sí mismo.

- Línea base: 59 pruebas, check y pip check correctos. Se reprodujo una pérdida visual de labores al editar el contexto: se generaba otro ID. La reproducción usó mocks, sin escribir Firebase.
- Resultado actual: 65 pruebas OK; `manage.py check` sin incidencias; `pip check` sin conflictos. Misma suite verificada en copia nueva con entorno virtual propio.
- Regresiones: conservar ID al modificar superficie, labor visible y modificable, aislamiento de otra sesión; 429 sin reintento y respaldo contextual; errores de red con un reintento; 5xx y red persistentes limitados a dos llamadas; solicitudes inválidas sin reintento; aviso veterinario incluso con contexto agrícola. Se corrigió también una prueba cuyo constructor podía ocultar el error simulado por falta de clave ficticia.
- La prueba existente confirma que un fallo de Firebase al finalizar la cuota no descarta una respuesta válida. Se mantienen pruebas de idempotencia, migración, reservas abandonadas, bloqueo ganadero, CSRF y longitudes.

| Consulta real en navegador | Tiempo completo | Resultado |
|---|---:|---|
| Riego de tomates en verano | 4,494 s | Gemini; observación de humedad y derivación técnica |
| Papas y heladas | 4,620 s | Gemini; advertencia de contexto Tomate |
| Labores semanales | 3,891 s | Gemini; labores relacionadas con el cultivo |
| Fertilizante para 500 m² | 4,776 s | Gemini; Estimación y dosis técnica, sin inventar cantidad |
| Vaca enferma y medicamento | 4,375 s | Gemini; derivación veterinaria sin medicamentos ni dosis |
| Vaca enferma desde copia limpia | 3,072 s | Gemini; aviso veterinario correcto y sin asteriscos Markdown |

Los tiempos incluyen el POST completo y el pronóstico. Modelo configurado: `gemini-3.5-flash-lite`; los logs no mostraron reintentos en esas consultas.

Persistencia real: contexto de prueba Maule/Tomate, tres labores y cambio de superficie 500 → 600 m²; lectura administrativa confirmó un solo ID de predio, las tres labores y una Hecha después de recargar. Se eliminaron exclusivamente las dos sesiones propias con marcador único `f84c`, verificando sus títulos y cantidad de labores. Las cuotas de las pruebas se conservaron: 11 intentos, 8 exitosas, 3 fallidas, 0 bloqueadas y 0 reservas pendientes al cierre. La cuota es global e incluye dos consultas anteriores a esta ejecución.

Fallos controlados: timeout simulado produjo dos llamadas y respaldo de riego de Tomate/Maule/600 m²; 429 simulado produjo una llamada y respaldo contextual inmediato. Ambos cerraron su cuota en Firebase real. Otro timeout y fallo de clima se verificaron en navegador: aviso local y aviso de Open-Meteo visibles, sin traza interna. Estos fallos fueron simulados, no caídas reales de los proveedores.

Open-Meteo real: tres días de Talca, fuente y actualización visibles. Estimación: 500 × 0,02 = 10 kg, fórmula y origen ficticio declarado. Superficie negativa: error de validación y HTTP 400 esperado. Sesión independiente: sin contexto ni acceso a labores ajenas. POST sin CSRF: HTTP 403 esperado.

Revisión visual antes/después: títulos móviles de 46,8 a 32 px, indicador de contexto alineado y salida sin marcadores de negrita; tipografía del sistema y controles de estado de 44 px. Paleta verde/tierra y estructura conservadas. Capturas en `docs/evidencias/fase-a-*.jpg`. Se revisaron contexto, consulta, labores y estimación; en las vistas medidas a 390 px no hubo ancho de contenido superior al viewport. Foco de teclado visible, formularios etiquetados y consola del navegador sin errores. No se trata de una certificación completa de accesibilidad.

Copia limpia: `Prueba Fase A 24 Noviembre`, ruta con espacios, entorno virtual nuevo. Los tres BAT funcionaron; consulta Gemini, clima, labor/estado y estimación reales comprobados. Se retiraron su `.env` y JSON temporales. Después, COMPROBAR e INICIAR devolvieron código 1 ante configuración ausente. Los BAT del compañero se leyeron dentro del RAR; no se ejecutaron ni se usaron sus credenciales. Se conservaron nuestros scripts y validaciones.

Seguridad: escaneo de archivos publicables, incluidos no versionados, sin claves Gemini, claves privadas, correo de servicio real, URL privada, rutas locales, bases SQLite, entornos, logs o ZIP. `git add --dry-run` revisado sin agregar archivos. Firebase REST sin credencial devolvió HTTP 401. Se mantienen las reglas locales de denegación; Admin SDK las omite y depende de IAM y validaciones del servidor.

Limitaciones: las respuestas de Gemini varían y requieren revisión profesional; el clima no se incorpora al prompt y se presenta como referencia separada. Sin autenticación ni recuperación de contexto al perder la cookie. Cuota global de 20, compartida con las pruebas. Las labores históricas asociadas a IDs anteriores no se migraron. Las dependencias directas están fijadas; las transitivas se resuelven durante instalación. La clave incluida en el RAR del compañero debe revocarse y nunca reutilizarse.

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

