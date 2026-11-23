# Auditoría preentrega de AgroAsistente

## Actualización posterior a la corrección final — 22 de noviembre de 2026

Los bloqueos descritos en la auditoría inicial fueron corregidos y verificados. La cuota v2 distingue intentos, exitosas, fallidas, bloqueadas, excesos y operaciones por ID; migra estructuras antiguas y finaliza de forma idempotente. Gemini usa timeout de 25 segundos, un reintento selectivo y categorías internas. Las 59 pruebas pasan. Cinco consultas reales respondieron con Gemini; un timeout doble forzado activó un respaldo relacionado y aumentó fallidas. El recorrido real cubrió contexto, tres labores, cambio a Hecha, estimación y Open-Meteo. La evidencia final autoritativa está en `RESULTADO_FINAL.md`, `PRUEBAS_Y_QA.md` y `MATRIZ_TRAZABILIDAD.md`.

El repositorio final y su clonación limpia se verificaron después de esta actualización: instalación nueva, 59 pruebas, BAT de arranque, Firebase, Gemini, Open-Meteo, labor y estimación funcionaron. Las credenciales temporales se retiraron del clon. Las observaciones históricas que aparecen más abajo se conservan para mostrar el diagnóstico previo y no describen el estado final.
Fecha de revisión: 22 de noviembre de 2026.

## Resumen ejecutivo

Estado ROJO para cerrar la entrega. Esta auditoría es parcial: se revisó código, el informe DOCX y documentación; se ejecutaron 30 pruebas y una instalación nueva. No se ejecutaron las cinco consultas en navegador ni el recorrido funcional de la copia limpia. Estos pendientes impiden certificar el cierre. No se modificó código ni se generó ZIP.

Las 30 pruebas pasan en el proyecto (0,807 s) y en un entorno virtual nuevo (1,372 s). Los mocks no demuestran funcionamiento del proveedor ni persistencia real bajo fallos. La documentación de QA conserva 28 pruebas y conclusiones históricas que no equivalen a aceptación actual.

## Inventario y arquitectura

Django recibe formularios, valida, guarda el contexto en sesión firmada y Firebase, invoca un Adapter Gemini/local y renderiza plantillas. No hay autenticación; la cookie identifica el contexto y visitante. Firebase Admin opera en servidor. La base SQL es dummy. Open-Meteo usa una coordenada representativa por región, no la ubicación exacta del predio.

Árbol resumido:

```
agroasistente/ settings.py, urls.py, asgi.py, wsgi.py
agro/ forms.py, constants.py, urls.py, views.py
  services/ orientation_provider.py, firebase_service.py,
            weather_service.py, estimacion_service.py
  tests/ test_forms.py, test_services.py, test_views.py,
         test_regresion_cuota.py
templates/agro/ base, inicio, consulta, labores, estimacion
static/agro/ styles.css, app.js
credentials/ README.txt (JSON local excluido)
docs/ DECISION_TECNICA, MATRIZ_TRAZABILIDAD, PRUEBAS_Y_QA, SEGURIDAD
  evidencias/ dos capturas históricas
scripts/ configurar_credenciales.sh
manage.py, requirements.txt, firebase.rules.json
.env.example, .gitignore, README.md, tres scripts BAT
```

Dependencias directas: Django 5.2.8, firebase-admin 7.1.0, google-genai 1.52.0, python-dotenv 1.2.1 y requests 2.32.5. Las transitivas no están fijadas.

Rutas: / → inicio; /contexto/ → configurar_contexto; /consulta/ → consulta; /labores/ → labores; /estimacion/ → estimacion. Configuración: settings.py, .env.example, firebase.rules.json, .gitignore. El .env y la credencial privada no se reproducen en este documento.

## Trazabilidad por sprint

Los criterios proceden del informe y de su matriz, no de una supuesta aceptación del usuario. El informe describe sprints propuestos, no ejecución histórica. Los nombres completos de pruebas están en el anexo.

| Sprint | HU | Criterio del informe | Archivo y función | Prueba automática | Prueba manual | Estado |
|---|---|---|---|---|---|---|
| 1 | HU-01 | Región válida y contexto de cultivo | forms.ContextoForm.clean; views.configurar_contexto | superficie; recorrido de contexto | Histórica; no repetida hoy | Implementada sin verificar |
| 1 | HU-02 | Pregunta válida y respuesta controlada | ConsultaForm; views.consulta; generar_orientacion | longitudes, respuesta local, regresión contable | Cinco consultas pendientes | Parcial |
| 1 | HU-03 | Falla recuperable sin claves ni trazas en pantalla | generar_orientacion; consulta | caída simulada y CSRF | Timeout real pendiente | Parcial |
| 2 | HU-04 | Guardar fecha y cambiar estado de tarea | crear_labor, listar_labores, cambiar_estado_labor | creación y cambio con mocks | Histórica; no repetida hoy | Implementada sin verificar |
| 2 | HU-05 | Cantidad, unidad, fórmula; rechazar negativos | EstimacionForm; calcular_cantidad; estimacion | fórmula y entradas inválidas | Histórica; copia nueva pendiente | Implementada sin verificar |
| 2 | HU-06 | Fuente y límites visibles | templates/agro/consulta.html y estimacion.html | cobertura de etiquetas incompleta | Histórica | Parcial |
| 3 | HU-07 | Pronóstico con fuente y actualización | weather_service.obtener_pronostico | timeout y estructura incompleta | No repetida hoy | Implementada sin verificar |
| 3 | HU-08 | Evitar indicaciones veterinarias | respuesta_ganadera_segura; AdaptadorLocal | dosis insegura y medicamento | Caso real pendiente | Parcial |
| 3 | HU-09 | Controlar consumo y excesos | firebase_service.reservar_cuota y confirmar_reserva | transacción simulada | Lectura del día: nodo ausente | Parcial |
| 4 | QA | Pruebas, interfaz, seguridad, recuperación, instalación y documentación | tests, BAT, docs, templates | 30 OK en dos entornos | Navegador y copia nueva pendientes | Parcial |

No se certifica ningún sprint cerrado en esta auditoría. HU-10 a HU-12 son opcionales y quedan fuera del juicio de cierre.

## Gemini: recorrido y hallazgos

ConsultaForm valida entre 10 y 300 caracteres. views.consulta llama generar_orientacion y luego obtiene el clima; la plantilla distingue gemini, bloqueada y local.

1. reservar_cuota realiza una transacción antes de construir el cliente.
2. AdaptadorGemini usa gemini-3.5-flash-lite, timeout de 10000 ms y max_output_tokens=700. No configura razonamiento explícitamente.
3. Se lee respuesta.text; texto vacío genera RuntimeError("Respuesta vacía").
4. La validación ganadera puede sustituir el texto y marcar tipo bloqueada.
5. confirmar_reserva registra éxito incluso cuando el texto quedó bloqueado por seguridad.
6. Una excepción del proveedor usa liberar_reserva y respaldo local. Solo se registra el nombre de clase; no la pregunta ni claves.
7. La confirmación contable ahora tiene try/except separado. Su fallo conserva la respuesta válida y muestra aviso. La prueba test_error_contable_no_descarta_respuesta_valida confirma este caso.

El SDK instalado usa retry_args(None): stop_after_attempt(1). El proyecto no configura retry_options: un intento, cero reintentos. Timeout, 429 y autenticación llegan al mismo respaldo; no hay clasificación específica. No se puede inferir de la etiqueta local qué error ocurrió. El fallo contable no descarta ya la respuesta, pero el filtro ganadero sí puede reemplazar texto válido por mera presencia de palabras como "tratamiento", incluso en una negativa segura.

Causa confirmada por regresión histórica: error de confirmación de Firebase descartaba texto válido; corregido. Causa de la consulta específica del usuario: pendiente de reproducción. Timeout de 10 segundos es una hipótesis, no una causa demostrada en esta auditoría.

## Cuota y transiciones

Ruta del código: consumo_ia/AAAA-MM-DD; fecha calculada con ZoneInfo("America/Santiago"). Lectura real de la fecha del host mediante fecha_chile(): None. Por tanto no se atribuye a Firebase un documento que no existe; la estructura siguiente es la que escribe el código.

Campos: exitosas, reservadas y excesos. No existen intentos ni fallidas en esta implementación. La interfaz muestra exitosas + reservadas bajo "Consultas externas hoy". No diferencia pendiente, éxito, fallo ni bloqueo de seguridad.

| Evento | reservadas | exitosas | excesos | Resultado |
|---|---:|---:|---:|---|
| Reserva admitida | +1 | igual | igual | Llama proveedor |
| Éxito | -1, mínimo 0 | +1 | igual | Gemini |
| Texto bloqueado por seguridad | -1 | +1 | igual | Bloqueada |
| Error o vacío | -1 | igual | igual | Local; fallo no registrado |
| Límite alcanzado | igual | igual | +1 en operación separada | Local sin llamada |
| Firebase falla al reservar | incierto si hubo commit | igual | igual | Local |
| Firebase falla al confirmar | puede quedar pendiente o haber confirmado | incierto | igual | Conserva Gemini con aviso |
| Firebase falla al liberar | puede quedar pendiente | igual | igual | Local; error silenciado |

La reserva protege atómicamente exitosas+reservadas contra concurrencia. No hay identificador de intento, finalización idempotente ni vencimiento de reservas. Una caída del proceso puede ocupar cuota hasta intervención manual. Un error de red después del commit hace ambiguo el resultado. Excesos se incrementa fuera de la transacción original y sus errores se silencian.

Compatibilidad antigua defectuosa: reservar_cuota y confirmar_reserva sustituyen un número por {} y pierden el histórico; obtener_consumo usa .get y falla sobre un número. liberar_reserva tampoco maneja números. No existe migración segura.

No hay incremento explícito de exitosas en la rama local actual. Sí se cuentan respuestas bloqueadas como exitosas; errores de red posteriores al commit y reservas huérfanas explican por qué un contador visible no demuestra éxito mostrado.

## Consultas reales solicitadas

No ejecutadas en navegador durante esta auditoría. No confundir con las consultas históricas ni con los mocks.

| Pregunta | Gemini llamado | Resultado Gemini | Adaptador mostrado | Intentos | Exitosas | Fallidas | Tiempo |
|---|---|---|---|---|---|---|---|
| ¿Cada cuánto debería regar tomates durante el verano? | No verificado | Pendiente | Pendiente | No implementado | No medido | No implementado | No medido |
| ¿Cómo puedo proteger mis papas de una helada? | No verificado | Pendiente | Pendiente | No implementado | No medido | No implementado | No medido |
| ¿Qué labores debería realizar esta semana? | No verificado | Pendiente | Pendiente | No implementado | No medido | No implementado | No medido |
| ¿Cuánto fertilizante necesito para 500 metros cuadrados? | No verificado | Pendiente | Pendiente | No implementado | No medido | No implementado | No medido |
| Mi vaca está enferma, ¿qué medicamento le puedo dar? | No verificado | Pendiente | Pendiente | No implementado | No medido | No implementado | No medido |

No se crearon registros funcionales temporales en Firebase en este turno.

## Respaldo local

Normaliza minúsculas y tildes con NFD, extrae palabras con regex y compara prefijos. La primera categoría coincidente gana; no combina intenciones ni considera negación.

- Riego prevalece sobre otras intenciones: "no quiero regar, necesito fertilizante" puede dar riego.
- "fertilizante para suelo" puede clasificarse como suelo por prioridad.
- "enferma" no coincide con "enfermo"; "medicamento" permite reconocer el ejemplo ganadero.
- El modo depende exclusivamente del contexto. Una pregunta veterinaria con contexto agrícola puede terminar en respuesta desconocida.
- Faltan variantes tierra, salinidad, plantación, temporada, recolección, frío/calor agrícolas y varios sinónimos pedidos.
- La región, cultivo y superficie se usan selectivamente. La pregunta no sustituye el cultivo configurado: mencionar papas con contexto Tomate puede producir una respuesta sobre Tomate.
- Fertilizante deriva a Estimación y dosis técnica; labores deriva a Labores.
- La respuesta agrícola desconocida declara limitación y conserva región/cultivo. La ganadera desconocida aún ofrece una lista genérica.
- El filtro veterinario no constituye una garantía completa de seguridad: bloquea términos seguros y puede dejar pasar expresiones no contempladas.

## Clonación limpia

Se creó una copia temporal con espacios a partir de git ls-files --cached --others --exclude-standard, limitada a la carpeta Django, sin .env, JSON privado ni entorno original. Se creó un entorno virtual nuevo, se instaló requirements.txt y se copió .env.example a .env.

Instalación: correcta. manage.py check: sin incidencias. manage.py test agro.tests: 30 OK, 1,372 s. No se colocaron credenciales reales ni se arrancó/verificó el recorrido desde navegador en esa copia. La prueba obligatoria de clonación está incompleta y el cierre queda bloqueado.

La copia temporal permanece en TEMP bajo "Agro Auditoria d7305a1c3ed04362901517d65164e0c7". Solo tiene ejemplos y dependencias; no contiene secretos reales copiados por esta auditoría.

Pasos manuales: instalar Python compatible; ejecutar INSTALAR_WINDOWS; generar DJANGO_SECRET_KEY propia; configurar URL Firebase y clave Gemini; copiar cuenta de servicio privada; comprobar y arrancar. La guía rápida omite generar el secreto Django. El profesor debe realizar estos mismos pasos tras clonar.

## GitHub y documentación

No es seguro aprobar git add . desde la raíz actual. git rev-parse confirma que la raíz es la carpeta superior a Django. La simulación desde esa raíz incluye .codex-staging-entrega y entregas anteriores; la simulación limitada a Django enumera los archivos públicos del anexo.

La exclusión de .env, credentials/*.json, venv y cachés está presente. No equivale a auditoría de secretos dentro de los ZIP antiguos ni de todo el historial. No se realizó una nueva inspección visual de las capturas; son evidencia histórica, no actual.

Transportar por separado .env y JSON privado, o preferiblemente configurar credenciales propias. No transportar .venv. Un compañero debe generar su propia cuenta de servicio, configurar URL y clave Gemini y secreto Django. Solo INSTALAR_WINDOWS crea .venv; los otros dos scripts requieren instalar primero.

README no coincide exactamente: afirma que el JSON permanece fuera del repositorio, aunque el asistente lo copia a credentials; la guía rápida indica solo dos valores, omitiendo el secreto Django; las cifras de QA siguen en 28. INSTALAR_WINDOWS no valida versión Python, ni sustituye automáticamente el secreto de ejemplo. INICIAR_WINDOWS solo verifica existencia de archivos, no validez de valores.

## Video

El informe DOCX menciona videos históricos de entrevistas y una referencia a material de rúbrica. No se encontró en el texto inspeccionado un requisito de video de demostración, duración o entrega. Esto no demuestra que una rúbrica separada no lo exija. Duración, contenido obligatorio y modalidad: no confirmados. No se añadió ningún video.

## Correcciones priorizadas y esfuerzo estimado

1. Bloqueante: cuota con intentos/exitosas/fallidas/excesos, migración y finalización idempotente; firebase_service, views._base y base.html. Estimación: 3–5 horas.
2. Bloqueante: reproducir cinco consultas con tiempos y excepción exacta, corregir timeout/reintento selectivo y respuesta vacía; orientation_provider y pruebas. 2–4 horas.
3. Importante: clasificación de intención y seguridad veterinaria, prioridad y contexto incoherente; AdaptadorLocal y pruebas. 2–3 horas.
4. Bloqueante para publicación: aislar raíz publicable, excluir ZIP/staging y escanear todos los archivos finales; .gitignore y proceso de entrega. 1–2 horas.
5. Importante: secreto Django, instalación y documentación coherentes; BAT, README, QA y matriz. 1–2 horas.
6. Bloqueante de aceptación: completar navegador real en copia limpia, errores controlados y evidencia. 2–3 horas.

Total orientativo: 11–19 horas de trabajo técnico, sujeto a disponibilidad del proveedor. No es garantía de cierre antes del martes 24.

## Anexo: código y configuración pública examinados

Los siguientes archivos completos permiten verificar las afirmaciones sin acceder a secretos.

### agro/services/orientation_provider.py
```
import os
import logging
import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

from .firebase_service import (
    FirebaseNoDisponible,
    LimiteDiarioAlcanzado,
    confirmar_reserva,
    liberar_reserva,
    reservar_cuota,
)


@dataclass
class ResultadoOrientacion:
    texto: str
    tipo: str
    aviso: str = ""


class ProveedorOrientacion(ABC):
    @abstractmethod
    def responder(self, contexto, pregunta):
        raise NotImplementedError


class AdaptadorLocal(ProveedorOrientacion):
    """Guía determinista por intención cuando el proveedor externo no responde."""

    TEMAS_AGRICOLAS = (
        ({"riego", "regar", "agua", "sequia", "seco", "seca", "humedad"}, "riego"),
        ({"hoja", "hojas", "amarilla", "amarillas", "mancha", "manchas", "plaga", "hongo", "enfermedad", "insecto"}, "sanidad"),
        ({"suelo", "fertilidad", "ph", "compactacion", "erosion"}, "suelo"),
        ({"fertilizante", "fertilizacion", "abono", "nutriente", "nitrogeno", "dosis", "insumo"}, "insumos"),
        ({"siembra", "sembrar", "plantar", "germinar", "germinacion", "semilla"}, "siembra"),
        ({"cosecha", "cosechar", "madurez", "maduro"}, "cosecha"),
        ({"helada", "lluvia", "temperatura", "clima", "viento", "pronostico"}, "clima"),
        ({"tarea", "actividad", "actividades", "labor", "trabajo", "semana"}, "labores"),
    )
    TEMAS_GANADEROS = (
        ({"agua", "calor", "sombra", "refugio", "frio"}, "ambiente"),
        ({"alimento", "alimentacion", "comer", "come", "forraje", "pasto"}, "alimentacion"),
        ({"enfermo", "enfermedad", "fiebre", "diarrea", "herida", "cojera", "sintoma"}, "salud"),
        ({"vacuna", "medicamento", "antibiotico", "tratamiento", "dosis"}, "tratamiento"),
        ({"parto", "prenada", "prenez", "reproduccion", "cria"}, "reproduccion"),
    )

    @staticmethod
    def _normalizar(texto):
        base = unicodedata.normalize("NFD", texto.lower())
        return "".join(c for c in base if unicodedata.category(c) != "Mn")

    @classmethod
    def _detectar_tema(cls, pregunta, grupos):
        palabras = set(re.findall(r"[a-zñ]+", cls._normalizar(pregunta)))
        for claves, tema in grupos:
            if any(palabra.startswith(clave) for palabra in palabras for clave in claves):
                return tema
        return "general"

    def responder(self, contexto, pregunta):
        region = contexto.get("region_nombre", "la región indicada")
        if contexto["modo"] == "Ganadera":
            tema = self._detectar_tema(pregunta, self.TEMAS_GANADEROS)
            respuestas = {
                "ambiente": (
                    f"Para revisar agua, sombra o refugio en {region}, comprueba disponibilidad continua de agua limpia, "
                    "zonas secas de descanso y protección frente al calor, frío o viento. Registra cambios de consumo y conducta."
                ),
                "alimentacion": (
                    "Ante una consulta de alimentación, observa si todos los animales acceden al alimento, cuánto consumen y si hay "
                    "cambios bruscos de apetito o condición corporal. Conserva una muestra o el rótulo del alimento para la revisión veterinaria."
                ),
                "salud": (
                    "Si observas signos de enfermedad, separa y registra al animal afectado sin indicar tratamientos por cuenta propia. "
                    "Anota inicio, conducta, consumo de agua y alimento y signos visibles; solicita evaluación de un médico veterinario."
                ),
                "tratamiento": (
                    "No es seguro definir medicamentos, vacunas, tratamientos o dosis mediante una guía local. Registra el peso aproximado, "
                    "los signos y su duración, y consulta a un médico veterinario antes de administrar cualquier producto."
                ),
                "reproduccion": (
                    "Para una consulta reproductiva, registra fechas, cambios de conducta, alimentación y signos observables. Mantén un lugar "
                    "limpio y tranquilo y solicita evaluación veterinaria si aparece dolor, sangrado o dificultad."
                ),
                "general": (
                    "No pude identificar un tema ganadero específico en la pregunta. Como revisión inicial, registra agua, alimento, refugio, "
                    "conducta y cualquier cambio reciente; con esos datos un médico veterinario podrá orientar el caso."
                ),
            }
        else:
            cultivo = contexto.get("cultivo_nombre", "el cultivo")
            superficie = contexto.get("superficie_m2", "no indicada")
            tema = self._detectar_tema(pregunta, self.TEMAS_AGRICOLAS)
            respuestas = {
                "riego": (
                    f"Para revisar el riego de {cultivo} en {region}, observa la humedad a pocos centímetros de profundidad en varios puntos, "
                    f"el drenaje y señales de marchitez. En los {superficie} m² registra sectores secos o encharcados y contrasta esas "
                    "observaciones con lluvia y temperatura antes de cambiar el riego."
                ),
                "sanidad": (
                    f"En hojas amarillas, manchas o posible plaga de {cultivo}, registra dónde comenzó el problema, cuántas plantas afecta y si "
                    "aparece en hojas nuevas o antiguas. Revisa el envés, toma fotografías y consulta a un ingeniero agrónomo antes de aplicar productos."
                ),
                "suelo": (
                    f"Para revisar el suelo y la fertilidad de {cultivo} en {region}, compara sectores del predio y registra drenaje, compactación, "
                    "materia orgánica visible y antecedentes del lote. Un análisis de suelo permite decidir con datos; no deduzcas una dosis solo por la apariencia."
                ),
                "insumos": (
                    f"Para estimar fertilizante o insumos en {superficie} m² de {cultivo}, abre la herramienta de Estimación e ingresa una dosis "
                    "verificada por la etiqueta, una fuente técnica o un ingeniero agrónomo. La orientación local no inventa dosis ni recomienda productos."
                ),
                "siembra": (
                    f"Antes de sembrar {cultivo} en {region}, revisa humedad y preparación del suelo, calidad de la semilla, profundidad recomendada "
                    "por su ficha técnica y el pronóstico de los próximos días. Registra la fecha y el lote utilizado."
                ),
                "cosecha": (
                    f"Para decidir la cosecha de {cultivo}, compara color, firmeza o humedad con la ficha técnica de la variedad y registra una muestra "
                    "representativa de distintos sectores. Evita decidir por una sola planta."
                ),
                "clima": (
                    f"Ante helada, lluvia o temperatura extrema en {region}, usa el pronóstico mostrado como referencia y revisa las zonas más expuestas. "
                    f"En {cultivo} joven, prepara protección física apropiada y registra daños después del evento. El pronóstico no garantiza la condición del predio."
                ),
                "general": (
                    f"La orientación local es limitada y no reconoció un tema específico sobre {cultivo} en {region}. Intenta reformular la consulta indicando "
                    "si se trata de riego, suelo, fertilizante, siembra, hojas o plagas, clima o cosecha."
                ),
                "labores": (
                    f"Para organizar esta semana los {superficie} m² de {cultivo} en {region}, revisa humedad, estado de plantas y pronóstico. "
                    "Anota las necesidades observadas en Labores, asigna fecha y actualiza su estado. "
                    "Sin conocer la etapa del cultivo, la guía local no puede fijar un calendario de siembra, aplicaciones o cosecha."
                ),
            }
        texto = respuestas[tema]
        return ResultadoOrientacion(texto=texto, tipo="local")


class AdaptadorGemini(ProveedorOrientacion):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Gemini no configurado")
        self.modelo = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.cliente = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=10000))

    def responder(self, contexto, pregunta):
        regla_ganadera = (
            "En modo ganadero no indiques tratamientos, medicamentos, antibióticos, vacunas ni dosis. "
            "Limítate a agua, sombra, refugio, registros y observación; deriva a un médico veterinario."
        )
        regla_agricola = (
            "No inventes dosis ni indiques aplicaciones concretas de plaguicidas. "
            "Para plagas, enfermedades o productos químicos deriva a un ingeniero agrónomo."
        )
        instruccion = regla_ganadera if contexto["modo"] == "Ganadera" else regla_agricola
        config = types.GenerateContentConfig(
            system_instruction=(
                "Eres un asistente de orientación general para pequeños productores de Chile. "
                f"Contexto: región {contexto['region_nombre']}, predio {contexto['predio']}, "
                f"modo {contexto['modo']}, cultivo {contexto['cultivo_nombre']}, superficie {contexto['superficie_m2']} m². "
                f"{instruccion} Responde en español, de forma breve, prudente y sin afirmar certeza profesional."
            ),
            max_output_tokens=700,
        )
        respuesta = self.cliente.models.generate_content(
            model=self.modelo,
            contents=pregunta.strip(),
            config=config,
        )
        texto = (respuesta.text or "").strip()
        if not texto:
            raise RuntimeError("Respuesta vacía")
        return ResultadoOrientacion(texto=texto, tipo="gemini")


PATRON_DOSIS = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mg|g|kg|ml|mL|l|cc)\b", re.IGNORECASE)
TERMINOS_MEDICACION = re.compile(r"\b(antibiótico|antibiotico|vacuna|inyecta|administrar|medicamento|tratamiento)\b", re.IGNORECASE)


def respuesta_ganadera_segura(texto):
    if PATRON_DOSIS.search(texto) or TERMINOS_MEDICACION.search(texto):
        return ("No se muestra la respuesta porque podría contener una indicación veterinaria concreta. "
                "Solicita la evaluación de un médico veterinario."), False
    return texto, True


def generar_orientacion(contexto, pregunta):
    limite = max(1, int(os.getenv("AI_DAILY_LIMIT", "20")))
    try:
        reservar_cuota(limite)
    except (LimiteDiarioAlcanzado, FirebaseNoDisponible):
        aviso = "Se usó la orientación local porque la cuota o su control no están disponibles."
        resultado = AdaptadorLocal().responder(contexto, pregunta)
        resultado.aviso = aviso
        return resultado

    try:
        resultado = AdaptadorGemini().responder(contexto, pregunta)
        if contexto["modo"] == "Ganadera":
            resultado.texto, segura = respuesta_ganadera_segura(resultado.texto)
            if not segura:
                resultado.tipo = "bloqueada"
                resultado.aviso = "La validación posterior bloqueó una respuesta ganadera insegura."
    except Exception as exc:
        logger.warning('Fallo de orientación: clase=%s', type(exc).__name__)
        liberar_reserva()
        resultado = AdaptadorLocal().responder(contexto, pregunta)
        resultado.aviso = "Gemini no estuvo disponible; se utilizó la orientación local."
        return resultado

    # Un fallo del contador no debe borrar una respuesta recibida.
    try:
        confirmar_reserva()
    except Exception as exc:
        logger.warning('Fallo de confirmación de cuota: clase=%s', type(exc).__name__)
        resultado.aviso = "La respuesta se recibió, pero no se pudo confirmar el contador de uso."
    return resultado
```
### agro/services/firebase_service.py
```
import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import firebase_admin
from firebase_admin import credentials, db


class FirebaseNoDisponible(Exception):
    pass


class LimiteDiarioAlcanzado(Exception):
    pass


_lock = threading.Lock()


def _inicializar():
    if firebase_admin._apps:
        return
    database_url = os.getenv("FIREBASE_DATABASE_URL", "").strip()
    if not database_url:
        raise FirebaseNoDisponible("Configuración de Firebase incompleta")
    try:
        with _lock:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.ApplicationDefault(), {"databaseURL": database_url})
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible conectar con Firebase") from exc


def _ref(ruta):
    _inicializar()
    try:
        return db.reference(ruta)
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible acceder a Firebase") from exc


def guardar_contexto(session_id, contexto):
    try:
        _ref(f"sesiones/{session_id}/contexto").set(contexto)
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible guardar el contexto") from exc


def crear_labor(session_id, contexto_id, labor):
    try:
        return _ref(f"sesiones/{session_id}/predios/{contexto_id}/labores").push(labor).key
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible guardar la labor") from exc


def listar_labores(session_id, contexto_id):
    try:
        datos = _ref(f"sesiones/{session_id}/predios/{contexto_id}/labores").get() or {}
        labores = [{"id": key, **value} for key, value in datos.items() if isinstance(value, dict)]
        return sorted(labores, key=lambda item: (item.get("fecha", ""), item.get("titulo", "")))
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible leer las labores") from exc


def cambiar_estado_labor(session_id, contexto_id, labor_id, estado):
    try:
        _ref(f"sesiones/{session_id}/predios/{contexto_id}/labores/{labor_id}").update({"estado": estado})
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible actualizar la labor") from exc


def fecha_chile():
    return datetime.now(ZoneInfo("America/Santiago")).date().isoformat()


def reservar_cuota(limite):
    referencia = _ref(f"consumo_ia/{fecha_chile()}")

    def reservar(actual):
        actual = actual if isinstance(actual, dict) else {}
        exitosas = int(actual.get("exitosas", 0))
        reservadas = int(actual.get("reservadas", 0))
        if exitosas + reservadas >= limite:
            raise LimiteDiarioAlcanzado
        actual["reservadas"] = reservadas + 1
        actual.setdefault("exitosas", exitosas)
        actual.setdefault("excesos", int(actual.get("excesos", 0)))
        return actual

    try:
        referencia.transaction(reservar)
    except LimiteDiarioAlcanzado:
        registrar_exceso()
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible reservar la cuota") from exc


def confirmar_reserva():
    referencia = _ref(f"consumo_ia/{fecha_chile()}")

    def confirmar(actual):
        actual = actual if isinstance(actual, dict) else {}
        actual["reservadas"] = max(0, int(actual.get("reservadas", 0)) - 1)
        actual["exitosas"] = int(actual.get("exitosas", 0)) + 1
        return actual

    referencia.transaction(confirmar)


def liberar_reserva():
    try:
        _ref(f"consumo_ia/{fecha_chile()}").transaction(
            lambda actual: {**(actual or {}), "reservadas": max(0, int((actual or {}).get("reservadas", 0)) - 1)}
        )
    except Exception:
        # La reserva expira operacionalmente al corregir el contador; se registra en logs desde la vista.
        pass


def registrar_exceso():
    try:
        _ref(f"consumo_ia/{fecha_chile()}/excesos").transaction(lambda actual: int(actual or 0) + 1)
    except Exception:
        pass


def obtener_consumo():
    try:
        actual = _ref(f"consumo_ia/{fecha_chile()}").get() or {}
        return int(actual.get("exitosas", 0)), int(actual.get("reservadas", 0))
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible consultar el consumo") from exc
```
### agro/views.py
```
import logging
import uuid
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import redirect, render

from .constants import CULTIVOS, REGION_NOMBRES
from .forms import ConsultaForm, ContextoForm, EstadoLaborForm, EstimacionForm, LaborForm
from .services import firebase_service
from .services.estimacion_service import calcular_cantidad
from .services.firebase_service import FirebaseNoDisponible
from .services.orientation_provider import generar_orientacion
from .services.weather_service import PronosticoNoDisponible, obtener_pronostico

logger = logging.getLogger(__name__)
CULTIVO_NOMBRES = dict(CULTIVOS)


def _session_id(request):
    if "visitante_id" not in request.session:
        request.session["visitante_id"] = uuid.uuid4().hex
    return request.session["visitante_id"]


def _contexto(request):
    return request.session.get("contexto")


def _base(request, **extra):
    contexto = _contexto(request)
    consumo = None
    try:
        exitosas, reservadas = firebase_service.obtener_consumo()
        consumo = {"usadas": exitosas + reservadas, "limite": max(1, int(__import__("os").getenv("AI_DAILY_LIMIT", "20")))}
    except Exception:
        pass
    return {"contexto": contexto, "consumo": consumo, **extra}


def inicio(request):
    _session_id(request)
    inicial = _contexto(request) or {}
    form = ContextoForm(initial=inicial)
    return render(request, "agro/inicio.html", _base(request, form=form))


def configurar_contexto(request):
    if request.method != "POST":
        return redirect("agro:inicio")
    form = ContextoForm(request.POST)
    if not form.is_valid():
        return render(request, "agro/inicio.html", _base(request, form=form), status=400)
    data = form.cleaned_data
    contexto = {
        "id": uuid.uuid4().hex,
        "region": data["region"],
        "region_nombre": REGION_NOMBRES[data["region"]],
        "predio": data["predio"].strip(),
        "modo": data["modo"],
        "cultivo": data["cultivo"],
        "cultivo_nombre": CULTIVO_NOMBRES.get(data["cultivo"], "No aplica"),
        "superficie_m2": str(data["superficie_m2"]),
    }
    request.session["contexto"] = contexto
    try:
        firebase_service.guardar_contexto(_session_id(request), contexto)
        messages.success(request, "Contexto guardado en Firebase.")
    except FirebaseNoDisponible:
        logger.warning("Firebase no disponible al guardar contexto")
        messages.warning(request, "El contexto quedó activo en esta sesión, pero Firebase no está disponible para persistirlo.")
    return redirect("agro:consulta")


def consulta(request):
    contexto = _contexto(request)
    if not contexto:
        messages.info(request, "Configura el contexto antes de realizar una consulta.")
        return redirect("agro:inicio")
    form = ConsultaForm(request.POST or None)
    resultado = pronostico = None
    error_pronostico = ""
    if request.method == "POST" and form.is_valid():
        pregunta = form.cleaned_data["pregunta"]
        try:
            resultado = generar_orientacion(contexto, pregunta)
        except Exception:
            logger.exception("Error controlado al generar orientación")
            messages.error(request, "No fue posible generar una orientación en este momento.")
        try:
            pronostico = obtener_pronostico(contexto["region"])
        except PronosticoNoDisponible:
            error_pronostico = "El pronóstico de Open-Meteo no está disponible en este momento."
    status = 400 if request.method == "POST" and not form.is_valid() else 200
    return render(request, "agro/consulta.html", _base(request, form=form, resultado=resultado, pronostico=pronostico, error_pronostico=error_pronostico), status=status)


def labores(request):
    contexto = _contexto(request)
    if not contexto:
        messages.info(request, "Configura el contexto antes de gestionar labores.")
        return redirect("agro:inicio")
    form = LaborForm()
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "crear":
            form = LaborForm(request.POST)
            if form.is_valid():
                labor = {"titulo": form.cleaned_data["titulo"].strip(), "fecha": form.cleaned_data["fecha"].isoformat(), "estado": "Pendiente"}
                try:
                    firebase_service.crear_labor(_session_id(request), contexto["id"], labor)
                    messages.success(request, "Labor agregada.")
                    return redirect("agro:labores")
                except FirebaseNoDisponible:
                    messages.error(request, "No fue posible guardar la labor porque Firebase no está disponible.")
        elif accion == "estado":
            estado_form = EstadoLaborForm(request.POST)
            if estado_form.is_valid():
                try:
                    firebase_service.cambiar_estado_labor(_session_id(request), contexto["id"], estado_form.cleaned_data["labor_id"], estado_form.cleaned_data["estado"])
                    messages.success(request, "Estado actualizado.")
                    return redirect("agro:labores")
                except FirebaseNoDisponible:
                    messages.error(request, "No fue posible actualizar la labor.")
    try:
        lista = firebase_service.listar_labores(_session_id(request), contexto["id"])
    except FirebaseNoDisponible:
        lista = []
        messages.warning(request, "No fue posible cargar las labores desde Firebase.")
    status = 400 if request.method == "POST" and form.errors else 200
    return render(request, "agro/labores.html", _base(request, form=form, labores=lista), status=status)


def estimacion(request):
    contexto = _contexto(request)
    initial = {}
    if contexto and Decimal(contexto.get("superficie_m2", "0")) > 0:
        initial["superficie_m2"] = contexto["superficie_m2"]
    form = EstimacionForm(request.POST or None, initial=initial)
    resultado = None
    if request.method == "POST" and form.is_valid():
        cantidad = calcular_cantidad(form.cleaned_data["superficie_m2"], form.cleaned_data["dosis_kg_m2"])
        resultado = {**form.cleaned_data, "cantidad": cantidad.quantize(Decimal("0.001"))}
    status = 400 if request.method == "POST" and not form.is_valid() else 200
    return render(request, "agro/estimacion.html", _base(request, form=form, resultado=resultado), status=status)
```
### agro/tests/test_services.py
```
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase

from agro.services.firebase_service import LimiteDiarioAlcanzado, reservar_cuota
from agro.services.orientation_provider import AdaptadorLocal, generar_orientacion, respuesta_ganadera_segura
from agro.services.weather_service import PronosticoNoDisponible, obtener_pronostico


CONTEXTO = {
    "region": "maule",
    "region_nombre": "Maule",
    "predio": "Los Robles",
    "modo": "Agrícola",
    "cultivo": "trigo",
    "cultivo_nombre": "Trigo",
    "superficie_m2": "1000",
}


class ServiciosTests(SimpleTestCase):
    def test_respaldo_local_responde_a_la_intencion_y_al_contexto(self):
        resultado = AdaptadorLocal().responder(
            CONTEXTO,
            "¿Cómo sé si debo regar el trigo esta semana?",
        )
        texto = resultado.texto.lower()
        self.assertIn("riego", texto)
        self.assertIn("trigo", texto)
        self.assertIn("maule", texto)

    def test_respaldo_local_para_hojas_amarillas_no_da_un_texto_de_riego(self):
        resultado = AdaptadorLocal().responder(
            CONTEXTO,
            "Las hojas se están poniendo amarillas y tienen manchas, ¿qué observo?",
        )
        texto = resultado.texto.lower()
        self.assertIn("hojas", texto)
        self.assertIn("manchas", texto)
        self.assertIn("ingeniero agrónomo", texto)

    def test_respaldo_local_distingue_riego_de_tomates(self):
        contexto = {**CONTEXTO, "cultivo_nombre": "Tomate"}
        texto = AdaptadorLocal().responder(
            contexto,
            "¿Cada cuánto tengo que regar mis tomates?",
        ).texto.lower()
        self.assertIn("riego", texto)
        self.assertIn("tomate", texto)
        self.assertNotIn("orientación local es limitada", texto)

    def test_respaldo_local_para_helada_da_medidas_prudentes(self):
        texto = AdaptadorLocal().responder(
            CONTEXTO,
            "¿Cómo puedo proteger el cultivo de una helada?",
        ).texto.lower()
        self.assertIn("helada", texto)
        self.assertIn("pronóstico", texto)

    def test_respaldo_local_de_fertilizante_deriva_a_estimacion(self):
        texto = AdaptadorLocal().responder(
            CONTEXTO,
            "¿Cuánto fertilizante necesito?",
        ).texto.lower()
        self.assertIn("estimación", texto)
        self.assertIn("dosis verificada", texto)

    def test_respaldo_local_de_suelo_no_inventa_fertilizante(self):
        texto = AdaptadorLocal().responder(
            CONTEXTO,
            "¿Cómo puedo revisar la fertilidad del suelo?",
        ).texto.lower()
        self.assertIn("suelo", texto)
        self.assertIn("análisis", texto)
        self.assertNotIn("herramienta de estimación", texto)

    def test_respaldo_ganadero_no_indica_medicamentos(self):
        contexto = {**CONTEXTO, "modo": "Ganadera", "cultivo_nombre": "No aplica"}
        texto = AdaptadorLocal().responder(
            contexto,
            "Mi vaca está enferma, ¿qué medicamento le doy?",
        ).texto.lower()
        self.assertIn("médico veterinario", texto)
        self.assertIn("no es seguro", texto)

    def test_respaldo_local_declara_limite_si_no_reconoce_la_pregunta(self):
        texto = AdaptadorLocal().responder(
            CONTEXTO,
            "¿Qué debería hacer hoy?",
        ).texto.lower()
        self.assertIn("orientación local es limitada", texto)
        self.assertIn("reformular", texto)

    @patch("agro.services.orientation_provider.liberar_reserva")
    @patch("agro.services.orientation_provider.reservar_cuota")
    @patch("agro.services.orientation_provider.AdaptadorGemini.responder", side_effect=RuntimeError("caída"))
    def test_respuesta_local_si_gemini_falla(self, gemini, reservar, liberar):
        resultado = generar_orientacion(CONTEXTO, "¿Cómo observo el riego del trigo?")
        self.assertEqual(resultado.tipo, "local")
        self.assertIn("Gemini no estuvo disponible", resultado.aviso)
        liberar.assert_called_once()

    @patch("agro.services.weather_service.requests.get", side_effect=requests.Timeout)
    def test_error_controlado_open_meteo(self, _get):
        with self.assertRaises(PronosticoNoDisponible):
            obtener_pronostico("maule")

    @patch("agro.services.orientation_provider.reservar_cuota", side_effect=LimiteDiarioAlcanzado)
    def test_limite_diario_usa_respaldo_local(self, _reservar):
        resultado = generar_orientacion(CONTEXTO, "¿Cómo observo el riego del trigo?")
        self.assertEqual(resultado.tipo, "local")
        self.assertIn("cuota", resultado.aviso)

    def test_bloquea_respuesta_ganadera_insegura(self):
        texto, segura = respuesta_ganadera_segura("Administre 5 ml de antibiótico cada día")
        self.assertFalse(segura)
        self.assertIn("médico veterinario", texto)

    @patch("agro.services.firebase_service.registrar_exceso")
    @patch("agro.services.firebase_service._ref")
    def test_reserva_de_cuota_es_una_transaccion(self, ref_factory, registrar_exceso):
        class ReferenciaFalsa:
            def __init__(self):
                self.valor = {"exitosas": 1, "reservadas": 0, "excesos": 0}

            def transaction(self, funcion):
                self.valor = funcion(self.valor)

        referencia = ReferenciaFalsa()
        ref_factory.return_value = referencia
        reservar_cuota(2)
        self.assertEqual(referencia.valor["reservadas"], 1)
        with self.assertRaises(LimiteDiarioAlcanzado):
            reservar_cuota(2)
        registrar_exceso.assert_called_once()

    @patch("agro.services.weather_service.requests.get")
    def test_pronostico_valida_respuesta_incompleta(self, get):
        respuesta = Mock()
        respuesta.raise_for_status.return_value = None
        respuesta.json.return_value = {"daily": {"time": []}}
        get.return_value = respuesta
        with self.assertRaises(PronosticoNoDisponible):
            obtener_pronostico("maule")
```
### agro/tests/test_regresion_cuota.py
```
from unittest.mock import patch

from django.test import SimpleTestCase

from agro.services.orientation_provider import AdaptadorLocal, ResultadoOrientacion, generar_orientacion
from agro.tests.test_services import CONTEXTO


class RegresionCuotaTests(SimpleTestCase):
    def test_labores_semanales_tienen_respaldo_relacionado(self):
        resultado = AdaptadorLocal().responder(CONTEXTO, '¿Qué labores debería realizar esta semana en mi predio?')
        self.assertIn('Labores', resultado.texto)
        self.assertIn('Maule', resultado.texto)
        self.assertNotIn('no reconoció', resultado.texto)

    @patch('agro.services.orientation_provider.liberar_reserva')
    @patch('agro.services.orientation_provider.confirmar_reserva', side_effect=RuntimeError('fallo de persistencia'))
    @patch('agro.services.orientation_provider.AdaptadorGemini.responder')
    @patch('agro.services.orientation_provider.reservar_cuota')
    def test_error_contable_no_descarta_respuesta_valida(self, reservar, responder, confirmar, liberar):
        responder.return_value = ResultadoOrientacion('Respuesta válida del proveedor', 'gemini')
        resultado = generar_orientacion(CONTEXTO, '¿Cómo revisar el riego?')
        self.assertEqual(resultado.tipo, 'gemini')
        self.assertEqual(resultado.texto, 'Respuesta válida del proveedor')
        liberar.assert_not_called()
```
### agro/tests/test_views.py
```
from unittest.mock import patch

from django.conf import settings
from django.test import Client, SimpleTestCase
from django.urls import reverse

from agro.services.orientation_provider import ResultadoOrientacion
from agro.services.weather_service import PronosticoNoDisponible


CONTEXTO = {
    "id": "predio-aleatorio",
    "region": "maule",
    "region_nombre": "Maule",
    "predio": "Los Robles",
    "modo": "Agrícola",
    "cultivo": "trigo",
    "cultivo_nombre": "Trigo",
    "superficie_m2": "1000",
}


class VistasTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def _con_contexto(self):
        sesion = self.client.session
        sesion["visitante_id"] = "visitante-prueba"
        sesion["contexto"] = CONTEXTO
        sesion.save()
        # El backend signed_cookies usa la sesión serializada como valor de cookie.
        self.client.cookies[settings.SESSION_COOKIE_NAME] = sesion.session_key

    @patch("agro.views.firebase_service.obtener_consumo", side_effect=Exception)
    def test_carga_pagina_principal(self, _consumo):
        respuesta = self.client.get(reverse("agro:inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Configura tu predio")

    @patch("agro.views.firebase_service.obtener_consumo", return_value=(0, 0))
    @patch("agro.views.firebase_service.guardar_contexto")
    def test_recorrido_configura_contexto_y_llega_a_consulta(self, guardar, _consumo):
        respuesta = self.client.post(
            reverse("agro:contexto"),
            {
                "region": "maule",
                "predio": "Los Robles",
                "modo": "Agrícola",
                "cultivo": "trigo",
                "superficie_m2": "1000",
            },
        )
        self.assertRedirects(respuesta, reverse("agro:consulta"), fetch_redirect_response=False)
        self.assertEqual(self.client.session["contexto"]["region_nombre"], "Maule")
        guardar.assert_called_once()

    @patch("agro.views.obtener_pronostico", side_effect=PronosticoNoDisponible("sin red"))
    @patch("agro.views.generar_orientacion", return_value=ResultadoOrientacion("Respuesta contextual", "local"))
    @patch("agro.views.firebase_service.obtener_consumo", return_value=(0, 0))
    def test_consulta_muestra_resultado_en_recorrido_configurado(self, _consumo, _orientacion, _clima):
        self._con_contexto()
        respuesta = self.client.post(reverse("agro:consulta"), {"pregunta": "¿Cómo debo observar el riego del trigo?"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Respuesta contextual")

    @patch("agro.views.firebase_service.listar_labores", return_value=[])
    @patch("agro.views.firebase_service.crear_labor", return_value="abc")
    @patch("agro.views.firebase_service.obtener_consumo", side_effect=Exception)
    def test_creacion_de_labor(self, _consumo, crear, _listar):
        self._con_contexto()
        respuesta = self.client.post(reverse("agro:labores"), {"accion": "crear", "titulo": "Regar", "fecha": "2026-11-18"})
        self.assertEqual(respuesta.status_code, 302)
        crear.assert_called_once()

    @patch("agro.views.firebase_service.listar_labores", return_value=[])
    @patch("agro.views.firebase_service.cambiar_estado_labor")
    @patch("agro.views.firebase_service.obtener_consumo", side_effect=Exception)
    def test_cambio_de_estado(self, _consumo, cambiar, _listar):
        self._con_contexto()
        respuesta = self.client.post(reverse("agro:labores"), {"accion": "estado", "labor_id": "abc", "estado": "Hecha"})
        self.assertEqual(respuesta.status_code, 302)
        cambiar.assert_called_once_with("visitante-prueba", "predio-aleatorio", "abc", "Hecha")

    def test_csrf_protege_contexto(self):
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse("agro:contexto"), {})
        self.assertEqual(respuesta.status_code, 403)

    def test_csrf_protege_consulta(self):
        cliente = Client(enforce_csrf_checks=True)
        sesion = cliente.session
        sesion["contexto"] = CONTEXTO
        sesion.save()
        cliente.cookies[settings.SESSION_COOKIE_NAME] = sesion.session_key
        respuesta = cliente.post(reverse("agro:consulta"), {"pregunta": "Una pregunta válida"})
        self.assertEqual(respuesta.status_code, 403)

    def test_csrf_protege_labores(self):
        cliente = Client(enforce_csrf_checks=True)
        sesion = cliente.session
        sesion["contexto"] = CONTEXTO
        sesion.save()
        cliente.cookies[settings.SESSION_COOKIE_NAME] = sesion.session_key
        respuesta = cliente.post(reverse("agro:labores"), {"accion": "crear", "titulo": "Regar", "fecha": "2026-11-18"})
        self.assertEqual(respuesta.status_code, 403)
```
### .gitignore
```
.env
*.env
!.env.example
*serviceAccount*.json
*ServiceAccount*.json
credentials/*.json
!credentials/README.txt
serviceAccountKey.json
ServiceAccountKey.json
*.pem
*.key
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
*.log
db.sqlite3
.DS_Store
.idea/
.vscode/
dist/
build/
```
### .env.example
```
DJANGO_SECRET_KEY=genere-una-clave-larga-y-unica
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
FIREBASE_DATABASE_URL=https://SU-PROYECTO-default-rtdb.firebaseio.com
FIREBASE_CREDENTIALS_PATH=credentials/firebase-admin.json
GEMINI_API_KEY=reemplace-con-una-clave-nueva
GEMINI_MODEL=gemini-3.5-flash-lite
AI_DAILY_LIMIT=20
```
### requirements.txt
```
Django==5.2.8
firebase-admin==7.1.0
google-genai==1.52.0
python-dotenv==1.2.1
requests==2.32.5
```
### INSTALAR_WINDOWS.bat
```
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

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno virtual...
    %PYTHON_CMD% -m venv .venv || goto :error
)

call ".venv\Scripts\activate.bat" || goto :error
python -m pip install --upgrade pip || goto :error
python -m pip install -r requirements.txt || goto :error

if not exist ".env" copy ".env.example" ".env" >nul
if not exist "credentials" mkdir "credentials"

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
```
### COMPROBAR_WINDOWS.bat
```
@echo off
setlocal
pushd "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Falta el entorno virtual. Ejecute primero INSTALAR_WINDOWS.bat.
    goto :error
)

call ".venv\Scripts\activate.bat" || goto :error
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
```
### INICIAR_WINDOWS.bat
```
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
echo La aplicacion estara disponible en http://127.0.0.1:8000/
python manage.py runserver 127.0.0.1:8000
set "SERVER_EXIT=%ERRORLEVEL%"
popd
exit /b %SERVER_EXIT%

:error
pause
popd
exit /b 1
```
### README.md
```
# AgroAsistente Chile

Aplicación web académica migrada desde el prototipo Streamlit a Django. Implementa HU-01 a HU-09 con Firebase Realtime Database como persistencia principal, Gemini mediante `google-genai`, respaldo local y pronóstico de Open-Meteo.

## Requisitos

- Python 3.11 o 3.12.
- Un proyecto nuevo de Firebase con Realtime Database.
- Una cuenta de servicio nueva guardada fuera del repositorio.
- Una clave nueva de Gemini, si se desea probar la integración real.

Las credenciales incluidas en entregas anteriores deben considerarse comprometidas y revocarse. No las reutilice.

## Instalación en Windows

Abra PowerShell en esta carpeta y ejecute:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` y reemplace todos los valores de ejemplo. Genere una clave de Django con:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Configuración segura de Firebase

Para realizar toda la configuración mediante un asistente interactivo, abra Git Bash en esta carpeta y ejecute:

```bash
bash scripts/configurar_credenciales.sh
```

El asistente abre los paneles oficiales, solicita las credenciales con entrada oculta, genera el secreto de Django y verifica Firebase, Gemini y Open-Meteo. El JSON de Firebase permanece fuera del repositorio.

1. Cree o seleccione un proyecto de Firebase que no use las credenciales antiguas.
2. Active Realtime Database.
3. En Google Cloud IAM, cree una cuenta de servicio con los permisos mínimos necesarios para ese proyecto.
4. Descargue un JSON nuevo, cópielo como `credentials/firebase-admin.json` y no lo suba al repositorio.
5. Mantenga `FIREBASE_CREDENTIALS_PATH=credentials/firebase-admin.json` y defina `FIREBASE_DATABASE_URL` con la URL de Realtime Database.
6. Publique `firebase.rules.json` para negar el acceso directo del cliente. El Admin SDK del servidor no depende de esas reglas; su seguridad también requiere IAM y validaciones del servidor.

El JSON puede estar en la carpeta local ignorada `credentials/`, pero nunca debe añadirse a Git ni al ZIP. La ruta relativa se resuelve desde `BASE_DIR`, aunque el servidor se inicie desde otro directorio.

## Variables de entorno

El archivo `.env.example` documenta:

- `FIREBASE_DATABASE_URL`
- `FIREBASE_CREDENTIALS_PATH`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `AI_DAILY_LIMIT`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`

El límite de Gemini es global para el prototipo porque no hay cuentas de usuario. La fecha se calcula en `America/Santiago`.

## Ejecución

```powershell
python manage.py check
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. Django usa sesiones firmadas en cookies; no usa SQLite como persistencia de negocio. Contextos, labores y contadores se almacenan en Firebase.

La aplicación carga sin credenciales y muestra errores recuperables. Sin Firebase no puede persistir contextos ni labores. Sin Gemini usa el adaptador local.

## Ejecución rápida en otro PC

1. Extraiga el ZIP en una carpeta local.
2. Ejecute `INSTALAR_WINDOWS.bat`.
3. Edite `.env` y configure `FIREBASE_DATABASE_URL` y `GEMINI_API_KEY`.
4. Copie una cuenta de servicio nueva como `credentials\firebase-admin.json`.
5. Ejecute `COMPROBAR_WINDOWS.bat` para validar el proyecto.
6. Ejecute `INICIAR_WINDOWS.bat` y abra `http://127.0.0.1:8000/`.

Los archivos `.env` y `credentials\firebase-admin.json` son locales y están ignorados por Git. No deben copiarse a un repositorio ni compartirse.

## Pruebas

```powershell
python manage.py test
```

Las pruebas usan mocks y no realizan llamadas reales a Firebase, Gemini u Open-Meteo.

## Estructura

- `agroasistente/`: configuración de Django.
- `agro/`: formularios, vistas, rutas, servicios y pruebas.
- `agro/services/firebase_service.py`: persistencia y cuota transaccional.
- `agro/services/orientation_provider.py`: Adapter para Gemini y respaldo local.
- `agro/services/weather_service.py`: Open-Meteo con timeout y validación.
- `templates/` y `static/`: interfaz responsive.
- `docs/`: decisiones, trazabilidad, QA y seguridad.

## Problemas comunes

- **Firebase no disponible:** revise `credentials/firebase-admin.json`, la URL de la base y los permisos IAM.
- **Gemini no disponible:** revise `GEMINI_API_KEY`, `GEMINI_MODEL` y la conectividad. El sistema continuará con orientación local.
- **Host no permitido:** añada el dominio a `DJANGO_ALLOWED_HOSTS`.
- **PowerShell bloquea la activación:** ejecute temporalmente `Set-ExecutionPolicy -Scope Process Bypass` y vuelva a activar el entorno.
- **Open-Meteo falla:** la aplicación informa el problema y conserva la orientación principal.

## Alcance y límites

HU-01 a HU-09 están representadas. HU-10, HU-11 y HU-12 no se implementaron. No existe autenticación; el aislamiento se realiza mediante un identificador aleatorio de sesión. No se guarda historial de preguntas. Las respuestas de Gemini se muestran como no verificadas y nunca se atribuyen a fuentes técnicas que no hayan fundamentado la respuesta.
```
### Inventario publicable
.env.example
.gitignore
COMPROBAR_WINDOWS.bat
INICIAR_WINDOWS.bat
INSTALAR_WINDOWS.bat
README.md
agro/__init__.py
agro/apps.py
agro/constants.py
agro/forms.py
agro/services/__init__.py
agro/services/estimacion_service.py
agro/services/firebase_service.py
agro/services/orientation_provider.py
agro/services/weather_service.py
agro/tests/__init__.py
agro/tests/test_forms.py
agro/tests/test_regresion_cuota.py
agro/tests/test_services.py
agro/tests/test_views.py
agro/urls.py
agro/views.py
agroasistente/__init__.py
agroasistente/asgi.py
agroasistente/settings.py
agroasistente/urls.py
agroasistente/wsgi.py
credentials/README.txt
docs/DECISION_TECNICA.md
docs/MATRIZ_TRAZABILIDAD.md
docs/PRUEBAS_Y_QA.md
docs/SEGURIDAD.md
docs/evidencias/escritorio-labores.png
docs/evidencias/movil-labores-390px.png
firebase.rules.json
manage.py
requirements.txt
scripts/configurar_credenciales.sh
static/agro/app.js
static/agro/styles.css
templates/agro/base.html
templates/agro/consulta.html
templates/agro/estimacion.html
templates/agro/inicio.html
templates/agro/labores.html

