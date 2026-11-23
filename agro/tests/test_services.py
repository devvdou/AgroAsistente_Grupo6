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
        self.assertIn("Gemini no respondió", resultado.aviso)
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

    @patch("agro.services.firebase_service._ref")
    def test_reserva_de_cuota_es_una_transaccion(self, ref_factory):
        class ReferenciaFalsa:
            def __init__(self):
                self.valor = {"exitosas": 1, "reservadas": 0, "excesos": 0}

            def transaction(self, funcion):
                self.valor = funcion(self.valor)
                return self.valor

        referencia = ReferenciaFalsa()
        ref_factory.return_value = referencia
        reservar_cuota(2)
        self.assertEqual(referencia.valor["intentos"], 2)
        with self.assertRaises(LimiteDiarioAlcanzado):
            reservar_cuota(2)
        self.assertEqual(referencia.valor['excesos'], 1)

    @patch("agro.services.weather_service.requests.get")
    def test_pronostico_valida_respuesta_incompleta(self, get):
        respuesta = Mock()
        respuesta.raise_for_status.return_value = None
        respuesta.json.return_value = {"daily": {"time": []}}
        get.return_value = respuesta
        with self.assertRaises(PronosticoNoDisponible):
            obtener_pronostico("maule")
