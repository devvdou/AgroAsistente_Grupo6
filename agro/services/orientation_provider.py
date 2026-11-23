import os
import logging
import re
import unicodedata
import time
import httpx
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
    reintentos: int = 0


class ConfiguracionGeminiError(Exception):
    pass


class RespuestaVaciaError(Exception):
    pass


def categoria_error(error):
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return 'timeout'
    if isinstance(error, ConfiguracionGeminiError):
        return 'configuracion'
    if isinstance(error, RespuestaVaciaError):
        return 'respuesta_vacia'
    codigo = getattr(error, 'code', None)
    if codigo == 429:
        return 'rate_limit'
    if codigo in (401, 403):
        return 'autenticacion'
    if codigo in (400, 404):
        return 'configuracion'
    if isinstance(codigo, int) and 500 <= codigo <= 599:
        return 'error_temporal'
    return 'error_desconocido'


class ProveedorOrientacion(ABC):
    @abstractmethod
    def responder(self, contexto, pregunta):
        raise NotImplementedError


class AdaptadorLocal(ProveedorOrientacion):
    """Guía determinista por intención cuando el proveedor externo no responde."""

    TEMAS_AGRICOLAS = (
        ({"riego", "regar", "agua", "sequia", "seco", "seca", "humedad"}, "riego"),
        ({"hoja", "hojas", "amarilla", "amarillas", "mancha", "manchas", "plaga", "hongo", "enfermedad", "insecto"}, "sanidad"),
        ({"suelo", "tierra", "salinidad", "drenaje", "fertilidad", "ph", "compactacion", "erosion"}, "suelo"),
        ({"fertilizante", "fertilizacion", "abono", "nutriente", "nitrogeno", "dosis", "insumo"}, "insumos"),
        ({"siembra", "sembrar", "plantar", "plantacion", "temporada", "germinar", "germinacion", "semilla"}, "siembra"),
        ({"cosecha", "cosechar", "recoleccion", "madurez", "maduro"}, "cosecha"),
        ({"helada", "frio", "calor", "lluvia", "temperatura", "clima", "viento", "pronostico"}, "clima"),
        ({"tarea", "actividad", "actividades", "labor", "trabajo", "semana"}, "labores"),
    )
    TEMAS_GANADEROS = (
        ({"agua", "calor", "sombra", "refugio", "frio"}, "ambiente"),
        ({"alimento", "alimentacion", "comer", "come", "forraje", "pasto"}, "alimentacion"),
        ({"enferm", "fiebre", "diarrea", "herida", "cojera", "sintoma"}, "salud"),
        ({"vacuna", "medicamento", "antibiotico", "tratamiento", "dosis"}, "tratamiento"),
        ({"parto", "prenada", "prenez", "reproduccion", "cria"}, "reproduccion"),
    )

    @staticmethod
    def _normalizar(texto):
        base = unicodedata.normalize("NFD", texto.lower())
        return "".join(c for c in base if unicodedata.category(c) != "Mn")

    @classmethod
    def _detectar_temas(cls, pregunta, grupos):
        normal = cls._normalizar(pregunta)
        normal = re.sub(r'\bno\s+(?:quiero\s+|necesito\s+|busco\s+|sobre\s+)?(?:regar\w*|riego\w*|fertiliz\w*|sembr\w*)', '', normal)
        palabras = set(re.findall(r"[a-zñ]+", normal))
        puntuaciones = []
        for claves, tema in grupos:
            puntos = sum(any(palabra.startswith(clave) for clave in claves) for palabra in palabras)
            if puntos:
                prioridad = {'tratamiento': 30, 'salud': 20, 'sanidad': 10}.get(tema, 0)
                puntuaciones.append((prioridad + puntos, tema))
        return [tema for _, tema in sorted(puntuaciones, reverse=True)[:2]] or ['general']

    @classmethod
    def es_ganadera(cls, contexto, pregunta):
        return contexto['modo'] == 'Ganadera' or bool(re.search(
            r'\b(vaca\w*|bovin\w*|animal\w*|ganado|oveja\w*|cerdo\w*)\b', cls._normalizar(pregunta)))

    def responder(self, contexto, pregunta):
        region = contexto.get("region_nombre", "la región indicada")
        aviso_contexto = ''
        if self.es_ganadera(contexto, pregunta):
            temas = self._detectar_temas(pregunta, self.TEMAS_GANADEROS)
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
                    f"La orientación local es limitada y no reconoce esta pregunta ganadera en {region}. "
                    "Puedes reformular sobre agua, refugio, alimentación, observación de salud o reproducción."
                ),
            }
        else:
            cultivo = contexto.get("cultivo_nombre", "el cultivo")
            mencionados = [nombre for nombre in ('Tomate', 'Papa', 'Trigo', 'Maíz', 'Avena', 'Cebolla', 'Lechuga')
                           if re.search(r'\b' + self._normalizar(nombre) + r'(?:s|es)?\b', self._normalizar(pregunta))]
            if mencionados and cultivo not in mencionados:
                aviso_contexto = f"Tu contexto indica {cultivo}, pero preguntas por {', '.join(mencionados)}. Confirma o edita el contexto. "
                cultivo = ', '.join(mencionados)
            superficie = contexto.get("superficie_m2", "no indicada")
            temas = self._detectar_temas(pregunta, self.TEMAS_AGRICOLAS)
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
        texto = aviso_contexto + ' '.join(respuestas[tema] for tema in temas)
        return ResultadoOrientacion(texto=texto, tipo="local")


class AdaptadorGemini(ProveedorOrientacion):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key.startswith('reemplace'):
            raise ConfiguracionGeminiError("Gemini no configurado")
        self.modelo = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.cliente = genai.Client(api_key=api_key, http_options=types.HttpOptions(
            timeout=25000, retry_options=types.HttpRetryOptions(attempts=1)))

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
                f"{instruccion} Responde en español, en un máximo de 90 palabras y tres pasos prácticos. "
                "No indiques frecuencia o dosis exacta sin datos técnicos. Si el cultivo preguntado difiere del contexto, adviértelo. "
                "Para cantidades de fertilizante dirige a Estimación con una dosis técnica verificada. "
                "Toda pregunta veterinaria requiere prudencia aunque el contexto sea agrícola."
            ),
            max_output_tokens=400,
            # Este SDK no enumera MINIMAL; conservamos el mínimo predeterminado del modelo.
        )
        try:
            for intento in range(2):
                try:
                    respuesta = self.cliente.models.generate_content(
                        model=self.modelo, contents=pregunta.strip(), config=config)
                    texto = (respuesta.text or '').strip()
                    if not texto:
                        raise RespuestaVaciaError('Respuesta vacía')
                    return ResultadoOrientacion(texto, 'gemini', reintentos=intento)
                except Exception as error:
                    categoria = categoria_error(error)
                    logger.warning('Gemini clase=%s categoria=%s', type(error).__name__, categoria)
                    if intento == 0 and categoria in ('timeout', 'rate_limit', 'error_temporal'):
                        time.sleep(0.5)
                        continue
                    raise
        finally:
            try:
                self.cliente.close()
            except Exception:
                pass


PATRON_DOSIS = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mg|g|kg|ml|mL|l|cc)\b", re.IGNORECASE)
TERMINOS_MEDICACION = re.compile(r"\b(antibiótico|antibiotico|vacuna|inyecta|administrar|medicamento|tratamiento)\b", re.IGNORECASE)


def respuesta_ganadera_segura(texto):
    normal = AdaptadorLocal._normalizar(texto)
    peligrosa = bool(PATRON_DOSIS.search(texto))
    for frase in re.split(r'[.!?;\n]+|\bpero\b', normal):
        segura = re.search(r'\bno\s+(?:\w+\s+){0,3}(?:administr\w*|aplic\w*|inyect\w*|recomendar\w*|usar\w*|dar\w*)', frase)
        segura = segura or ('veterinario' in frase and re.search(r'consulta|antes de|solo|supervision', frase))
        indicacion = re.search(r'\b(?:administ\w*|inyect\w*|aplic\w*|suminist\w*|dale|darle|usa|usar|recomiendo)\b', frase)
        producto = re.search(r'medicament|antibiotic|vacun|tratamiento|penicilina|ivermectina|amoxicilina', frase)
        peligrosa = peligrosa or bool(producto and not segura and (indicacion or re.search(r'\b(?:con|usar|dar)\b', frase)))
    if peligrosa:
        return ("No se muestra la respuesta porque podría contener una indicación veterinaria concreta. "
                "Solicita la evaluación de un médico veterinario."), False
    return texto, True


def generar_orientacion(contexto, pregunta):
    limite = max(1, int(os.getenv("AI_DAILY_LIMIT", "20")))
    try:
        reserva = reservar_cuota(limite)
    except (LimiteDiarioAlcanzado, FirebaseNoDisponible):
        aviso = "Se usó la orientación local porque la cuota o su control no están disponibles."
        resultado = AdaptadorLocal().responder(contexto, pregunta)
        resultado.aviso = aviso
        return resultado

    try:
        resultado = AdaptadorGemini().responder(contexto, pregunta)
        if AdaptadorLocal.es_ganadera(contexto, pregunta):
            resultado.texto, segura = respuesta_ganadera_segura(resultado.texto)
            if not segura:
                resultado.tipo = "bloqueada"
                resultado.aviso = "La validación posterior bloqueó una respuesta ganadera insegura."
    except Exception as exc:
        logger.warning('Fallo de orientación: clase=%s categoria=%s', type(exc).__name__, categoria_error(exc))
        try:
            liberar_reserva(reserva)
        except FirebaseNoDisponible as error:
            logger.warning('Fallo contable: clase=%s', type(error).__name__)
        resultado = AdaptadorLocal().responder(contexto, pregunta)
        resultado.aviso = "Gemini no respondió. Se está mostrando una orientación local."
        return resultado

    # Un fallo del contador no debe borrar una respuesta recibida.
    try:
        confirmar_reserva(reserva, bloqueada=resultado.tipo == 'bloqueada')
    except Exception as exc:
        logger.warning('Fallo de confirmación de cuota: clase=%s', type(exc).__name__)
        resultado.aviso = "La respuesta se recibió, pero no se pudo confirmar el contador de uso."
    return resultado
