from unittest.mock import Mock, patch
import httpx
from google.genai import errors
from django.test import SimpleTestCase
from agro.services import orientation_provider as p
from agro.tests.test_services import CONTEXTO


class GeminiFinalTests(SimpleTestCase):
    def ejecutar(self, efectos):
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'clave-ficticia-para-test'}), patch.object(p.genai, 'Client') as cliente, patch.object(p.time, 'sleep'):
            llamada = cliente.return_value.models.generate_content
            llamada.side_effect = efectos
            try:
                resultado = p.AdaptadorGemini().responder(CONTEXTO, '¿Cómo revisar el riego?')
                return resultado, llamada.call_count
            except Exception as error:
                return error, llamada.call_count

    def test_exito(self):
        r, n = self.ejecutar([Mock(text='Observa la humedad.')])
        self.assertEqual((r.tipo, r.reintentos, n), ('gemini', 0, 1))

    def test_timeout_reintenta_una_vez(self):
        r, n = self.ejecutar([httpx.ReadTimeout('prueba'), Mock(text='Respuesta')])
        self.assertEqual((r.tipo, r.reintentos, n), ('gemini', 1, 2))

    def test_429_reintenta(self):
        r, n = self.ejecutar([errors.ClientError(429, {}), Mock(text='Respuesta')])
        self.assertEqual((r.tipo, n), ('gemini', 2))

    def test_503_reintenta(self):
        r, n = self.ejecutar([errors.ServerError(503, {}), Mock(text='Respuesta')])
        self.assertEqual((r.tipo, n), ('gemini', 2))

    def test_autenticacion_no_reintenta(self):
        for codigo in (401, 403):
            r, n = self.ejecutar([errors.ClientError(codigo, {})])
            self.assertEqual((p.categoria_error(r), n), ('autenticacion', 1))

    def test_configuracion_no_reintenta(self):
        r, n = self.ejecutar([errors.ClientError(400, {})])
        self.assertEqual((p.categoria_error(r), n), ('configuracion', 1))

    def test_vacio_no_reintenta(self):
        r, n = self.ejecutar([Mock(text='')])
        self.assertEqual((p.categoria_error(r), n), ('respuesta_vacia', 1))

    def test_desconocido_no_reintenta(self):
        r, n = self.ejecutar([RuntimeError('prueba')])
        self.assertEqual((p.categoria_error(r), n), ('error_desconocido', 1))

    def test_timeout_persistente_termina(self):
        r, n = self.ejecutar([TimeoutError(), TimeoutError()])
        self.assertEqual((p.categoria_error(r), n), ('timeout', 2))

    def test_clave_ausente(self):
        with patch.dict('os.environ', {'GEMINI_API_KEY': ''}), patch.object(p.genai, 'Client') as cliente:
            with self.assertRaises(p.ConfiguracionGeminiError):
                p.AdaptadorGemini()
            cliente.assert_not_called()

    def test_finalizacion_por_resultado(self):
        for texto, modo, esperado in [('Observa el suelo', 'Agrícola', 'gemini'), ('Administra 5 ml de antibiótico', 'Ganadera', 'bloqueada')]:
            with patch.dict('os.environ', {'GEMINI_API_KEY': 'clave-ficticia-para-test'}), patch.object(p.genai, 'Client'), patch.object(p, 'reservar_cuota', return_value=('2026-11-22', 'id')), patch.object(p.AdaptadorGemini, 'responder', return_value=p.ResultadoOrientacion(texto, 'gemini')), patch.object(p, 'confirmar_reserva') as confirmar:
                r = p.generar_orientacion({**CONTEXTO, 'modo': modo}, 'Consulta de prueba')
                self.assertEqual(r.tipo, esperado)
                confirmar.assert_called_once_with(('2026-11-22', 'id'), bloqueada=esperado == 'bloqueada')

    def test_fallo_finaliza_fallida(self):
        for error in (TimeoutError(), p.RespuestaVaciaError(), errors.ClientError(403, {})):
            with patch.object(p, 'reservar_cuota', return_value=('fecha', 'id')), patch.object(p.AdaptadorGemini, 'responder', side_effect=error), patch.object(p, 'liberar_reserva') as fallar, patch.object(p, 'confirmar_reserva') as confirmar:
                self.assertEqual(p.generar_orientacion(CONTEXTO, '¿Cómo regar?').tipo, 'local')
                fallar.assert_called_once_with(('fecha', 'id'))
                confirmar.assert_not_called()

    def test_limite_no_llama_proveedor(self):
        with patch.object(p, 'reservar_cuota', side_effect=p.LimiteDiarioAlcanzado), patch.object(p, 'AdaptadorGemini') as cliente:
            self.assertEqual(p.generar_orientacion(CONTEXTO, '¿Cómo regar?').tipo, 'local')
            cliente.assert_not_called()

    def test_negativas_seguras(self):
        for texto in ('No administres medicamentos', 'No puedo recomendar un tratamiento', 'Consulta a un veterinario antes de aplicar una dosis', 'Revisa agua, sombra, refugio y conducta'):
            self.assertTrue(p.respuesta_ganadera_segura(texto)[1], texto)

    def test_indicaciones_inseguras(self):
        for texto in ('Administra 5 ml', 'Inyecta un antibiótico', 'Aplica la vacuna', 'Recomiendo tratamiento con penicilina'):
            self.assertFalse(p.respuesta_ganadera_segura(texto)[1], texto)

    def test_dos_intenciones(self):
        r = p.AdaptadorLocal().responder(CONTEXTO, '¿Cómo revisar riego y fertilizante?')
        self.assertIn('riego', r.texto)
        self.assertIn('Estimación', r.texto)

    def test_negacion(self):
        r = p.AdaptadorLocal().responder(CONTEXTO, 'No quiero regar, necesito fertilizante')
        self.assertIn('Estimación', r.texto)
        self.assertNotIn('Para revisar el riego', r.texto)

    def test_cultivo_contradictorio(self):
        r = p.AdaptadorLocal().responder({**CONTEXTO, 'cultivo_nombre': 'Tomate'}, '¿Cómo proteger mis papas de una helada?')
        self.assertIn('contexto indica Tomate', r.texto)
        self.assertIn('Papa', r.texto)

    def test_variantes(self):
        for pregunta, tema in [('enferma', 'salud'), ('tierra salinidad', 'suelo'), ('plantación temporada', 'siembra'), ('recolección', 'cosecha'), ('frío calor', 'clima')]:
            grupos = p.AdaptadorLocal.TEMAS_GANADEROS if tema == 'salud' else p.AdaptadorLocal.TEMAS_AGRICOLAS
            self.assertIn(tema, p.AdaptadorLocal._detectar_temas(pregunta, grupos))

    def test_veterinaria_aunque_contexto_agricola(self):
        r = p.AdaptadorLocal().responder(CONTEXTO, 'Mi vaca está enferma, ¿qué medicamento le doy?')
        self.assertIn('médico veterinario', r.texto)
