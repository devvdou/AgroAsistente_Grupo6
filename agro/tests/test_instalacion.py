import tempfile
from pathlib import Path
from django.test import SimpleTestCase
from dotenv import dotenv_values
from scripts.configuracion_local import preparar, comprobar


class InstalacionTests(SimpleTestCase):
    def test_genera_secreto_y_no_sobrescribe_configuracion(self):
        with tempfile.TemporaryDirectory() as carpeta:
            base = Path(carpeta)
            (base / '.env.example').write_text('DJANGO_SECRET_KEY=genere-una-clave-larga-y-unica\nGEMINI_API_KEY=reemplace-con-una-clave-nueva\n', encoding='utf-8')
            preparar(base)
            primera = (base / '.env').read_bytes()
            self.assertGreater(len(dotenv_values(base / '.env')['DJANGO_SECRET_KEY']), 40)
            preparar(base)
            self.assertEqual((base / '.env').read_bytes(), primera)

    def test_detecta_credencial_y_valores_faltantes_sin_exponerlos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            base = Path(carpeta)
            (base / '.env').write_text('DJANGO_SECRET_KEY=secreto-no-mostrar\n', encoding='utf-8')
            mensajes = ' '.join(comprobar(base))
            self.assertIn('GEMINI_API_KEY', mensajes)
            self.assertIn('cuenta de servicio', mensajes)
            self.assertNotIn('secreto-no-mostrar', mensajes)
