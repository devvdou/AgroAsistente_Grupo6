from django.test import SimpleTestCase
from agro.services.quota_state import iniciar, finalizar, normalizar


class EstadoCuotaTests(SimpleTestCase):
    def test_migra_numero_sin_perder_consumo(self):
        data = normalizar(7, 1000)
        self.assertEqual((data['intentos'], data['exitosas']), (7, 7))

    def test_migra_reservas_antiguas_como_abandonadas(self):
        data = normalizar({'exitosas': 3, 'reservadas': 2, 'excesos': 4}, 1000)
        self.assertEqual((data['intentos'], data['fallidas'], data['excesos']), (5, 2, 4))
        self.assertEqual(normalizar(data, 1000), data)

    def test_finalizacion_idempotente(self):
        data = iniciar(None, 'a', 20, 1000)
        data = finalizar(data, 'a', 'exitosa', 1001)
        self.assertEqual(finalizar(data, 'a', 'fallida', 1002), data)
        self.assertEqual((data['intentos'], data['exitosas'], data['fallidas']), (1, 1, 0))

    def test_dos_reservas_serializadas_respetan_limite(self):
        data = iniciar(None, 'a', 1, 1000)
        data = iniciar(data, 'b', 1, 1000)
        self.assertEqual((data['intentos'], data['excesos']), (1, 1))
        self.assertEqual(data['operaciones']['b']['estado'], 'rechazada')
        self.assertEqual(iniciar(data, 'b', 1, 1000), data)

    def test_abandonada_se_cuenta_una_vez(self):
        data = normalizar(iniciar(None, 'a', 20, 1000), 1400)
        self.assertEqual(data['fallidas'], 1)
        self.assertEqual(finalizar(data, 'a', 'exitosa', 1401)['exitosas'], 0)

    def test_bloqueada_no_es_respuesta_exitosa(self):
        data = finalizar(iniciar(None, 'a', 20, 1000), 'a', 'bloqueada', 1001)
        self.assertEqual((data['bloqueadas'], data['exitosas']), (1, 0))
