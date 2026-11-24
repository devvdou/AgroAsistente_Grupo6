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
    @patch('agro.views.obtener_pronostico', side_effect=PronosticoNoDisponible('prueba'))
    @patch('agro.views.generar_orientacion', return_value=ResultadoOrientacion('Consulta a un veterinario.', 'gemini'))
    @patch('agro.views.firebase_service.obtener_consumo', return_value={})
    def test_pregunta_animal_muestra_aviso_veterinario_en_contexto_agricola(self, consumo, orientacion, clima):
        self._con_contexto()
        respuesta = self.client.post(reverse('agro:consulta'), {'pregunta': 'Mi vaca está enferma, ¿qué hago?'})
        self.assertContains(respuesta, 'requieren un médico veterinario')
        self.assertNotContains(respuesta, 'requieren un ingeniero agrónomo')

    @patch('agro.views.obtener_pronostico', side_effect=PronosticoNoDisponible('prueba'))
    @patch('agro.views.firebase_service.obtener_consumo', return_value={'intentos': 3, 'exitosas': 1, 'fallidas': 1, 'bloqueadas': 1})
    def test_etiquetas_y_contadores_reflejan_resultado(self, consumo, clima):
        self._con_contexto()
        for tipo, etiqueta in [('gemini', 'Respuesta generada por Gemini'), ('local', 'Orientación local de respaldo'), ('bloqueada', 'Respuesta bloqueada por seguridad')]:
            with patch('agro.views.generar_orientacion', return_value=ResultadoOrientacion('Texto de prueba', tipo)):
                respuesta = self.client.post(reverse('agro:consulta'), {'pregunta': '¿Cómo revisar el cultivo?'})
                self.assertContains(respuesta, etiqueta)
                self.assertContains(respuesta, 'Intentos de IA hoy: 3/20')
                self.assertContains(respuesta, 'Fallidas: 1')

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
