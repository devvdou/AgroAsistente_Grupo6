from decimal import Decimal

from django.test import SimpleTestCase

from agro.forms import ConsultaForm, ContextoForm, EstimacionForm
from agro.services.estimacion_service import calcular_cantidad


class ValidacionesTests(SimpleTestCase):
    def test_consulta_vacia(self):
        self.assertFalse(ConsultaForm({"pregunta": ""}).is_valid())

    def test_consulta_menor_al_minimo(self):
        self.assertFalse(ConsultaForm({"pregunta": "corta"}).is_valid())

    def test_consulta_superior_al_maximo(self):
        self.assertFalse(ConsultaForm({"pregunta": "x" * 301}).is_valid())

    def test_superficie_cero_o_negativa(self):
        base = {"region": "maule", "predio": "Los Robles", "modo": "Agrícola", "cultivo": "trigo"}
        self.assertFalse(ContextoForm({**base, "superficie_m2": "0"}).is_valid())
        self.assertFalse(ContextoForm({**base, "superficie_m2": "-1"}).is_valid())

    def test_dosis_cero_o_negativa(self):
        base = {"superficie_m2": "100", "unidad": "kg/m²", "origen_dosis": "Etiqueta técnica"}
        self.assertFalse(EstimacionForm({**base, "dosis_kg_m2": "0"}).is_valid())
        self.assertFalse(EstimacionForm({**base, "dosis_kg_m2": "-0.1"}).is_valid())

    def test_formula_estimacion(self):
        self.assertEqual(calcular_cantidad("125.5", "0.04"), Decimal("5.020"))
