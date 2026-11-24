from copy import deepcopy
from unittest.mock import patch

from django.test import Client, SimpleTestCase


class ContextoEstableTests(SimpleTestCase):
    def test_editar_contexto_conserva_labor_visible_y_modificable(self):
        contextos, labores = {}, {}

        def guardar(sesion, contexto):
            contextos[sesion] = deepcopy(contexto)

        def crear(sesion, predio, labor):
            labores[(sesion, predio)] = {'id': 'labor-prueba', **labor}

        def listar(sesion, predio):
            labor = labores.get((sesion, predio))
            return [labor] if labor else []

        def cambiar(sesion, predio, identificador, estado):
            self.assertEqual(labores[(sesion, predio)]['id'], identificador)
            labores[(sesion, predio)]['estado'] = estado

        with patch('agro.views.firebase_service.obtener_consumo', return_value={}), patch('agro.views.firebase_service.guardar_contexto', side_effect=guardar), patch('agro.views.firebase_service.crear_labor', side_effect=crear), patch('agro.views.firebase_service.listar_labores', side_effect=listar), patch('agro.views.firebase_service.cambiar_estado_labor', side_effect=cambiar):
            cliente = Client()
            contexto = {'region': 'maule', 'predio': 'Los Robles', 'modo': 'Agrícola', 'cultivo': 'tomate', 'superficie_m2': '500'}
            self.assertEqual(cliente.post('/contexto/', contexto).status_code, 302)
            identificador = cliente.session['contexto']['id']
            sesion = cliente.session['visitante_id']
            self.assertEqual(cliente.post('/labores/', {'accion': 'crear', 'titulo': 'Revisar riego', 'fecha': '2026-11-24'}).status_code, 302)
            self.assertContains(cliente.get('/labores/'), 'Revisar riego')
            self.assertEqual(cliente.post('/contexto/', {**contexto, 'superficie_m2': '600'}).status_code, 302)
            self.assertEqual(cliente.session['contexto']['id'], identificador)
            self.assertEqual(contextos[sesion]['id'], identificador)
            self.assertEqual(contextos[sesion]['superficie_m2'], '600')
            self.assertContains(cliente.get('/labores/'), 'Revisar riego')
            self.assertEqual(cliente.post('/labores/', {'accion': 'estado', 'labor_id': 'labor-prueba', 'estado': 'Hecha'}).status_code, 302)
            self.assertEqual(labores[(sesion, identificador)]['estado'], 'Hecha')
            self.assertContains(cliente.get('/labores/'), 'Revisar riego')
            otro = Client()
            self.assertRedirects(otro.get('/labores/'), '/', fetch_redirect_response=False)
            otro.post('/contexto/', contexto)
            self.assertNotEqual(otro.session['contexto']['id'], identificador)
            self.assertNotContains(otro.get('/labores/'), 'Revisar riego')
