# Matriz de trazabilidad final

Actualización del 24 de noviembre: HU-01/HU-04 verificadas conservando el ID y tres labores tras editar superficie, con estado Hecha persistido. HU-02/HU-06/HU-07/HU-08: cinco consultas reales, pronóstico de tres días, fórmula de 10 kg y negativa veterinaria. HU-03/HU-09: timeout controlado, 429 sin reintento, cuota real sin reservas pendientes y pruebas de idempotencia. Sprint 4: 65 pruebas OK, copia limpia con BAT y revisión a 390 px. Evidencia detallada en `PRUEBAS_Y_QA.md`; prueba manual aceptada y empaquetado autorizado por el usuario. Publicación pendiente de coordinación.

Evidencia obtenida el 22 de noviembre de 2026. “Completa y verificada” exige prueba automática y recorrido manual real.

| HU | Sprint | Criterio | Implementación | Evidencia | Estado |
|---|---:|---|---|---|---|
| HU-01 | 1 | Contexto regional, predio, modo, cultivo y superficie | `ContextoForm`, sesión firmada y Firebase | Validaciones + contexto Maule/Tomate y Ganadera guardado desde navegador | Completa y verificada |
| HU-02 | 1 | Consulta válida y respuesta controlada | `ConsultaForm`, Adapter Gemini/local | Longitudes + cinco respuestas reales de Gemini | Completa y verificada |
| HU-03 | 1 | Fallas y límites recuperables | Categorías internas, reintento y respaldo | Pruebas de timeout/429/5xx/auth/vacía + timeout forzado en navegador | Completa y verificada |
| HU-04 | 2 | Crear, listar y cambiar estado de labores | `firebase_service`, `views.labores` | Pruebas + tres labores reales y una Hecha | Completa y verificada |
| HU-05 | 2 | Superficie × dosis, unidad, fórmula y origen | `EstimacionForm`, `calcular_cantidad` | Pruebas + 500 × 0,02 = 10 kg en navegador | Completa y verificada |
| HU-06 | 2 | Fuentes, límites y advertencias visibles | Plantillas de consulta y estimación | Etiquetas Gemini/local/bloqueada + Open-Meteo atribuido | Completa y verificada |
| HU-07 | 3 | Pronóstico con fuente, localidad y actualización | `weather_service.obtener_pronostico` | Errores simulados + tres días reales para Talca | Completa y verificada |
| HU-08 | 3 | Ganadería sin tratamientos ni dosis | Prompt, filtro posterior y respaldo local | Negativas seguras, bloqueos inseguros y consulta veterinaria real | Completa y verificada |
| HU-09 | 3 | Consumo y exceso atómicos | ID por intento, migración, finalización idempotente | Pruebas de límite/migración/concurrencia conceptual + contador real 6/5/1 | Completa y verificada |

Sprint 4: 65 pruebas, interfaz de escritorio y móvil, CSRF, scripts reproducibles, repositorio aislado, clonación limpia y escaneo de secretos. HU-10 a HU-12 permanecen fuera del alcance.

