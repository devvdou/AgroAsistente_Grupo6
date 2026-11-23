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
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'clave-ficticia-para-test'}), patch('agro.services.orientation_provider.genai.Client'):
            resultado = generar_orientacion(CONTEXTO, '¿Cómo revisar el riego?')
        self.assertEqual(resultado.tipo, 'gemini')
        self.assertEqual(resultado.texto, 'Respuesta válida del proveedor')
        liberar.assert_not_called()
