# Seguridad del prototipo

`.env`, cuentas de servicio, claves privadas, entornos, ZIP, cachés y logs están ignorados. La clave Gemini y el JSON Firebase solo se usan en el servidor. El instalador genera un secreto Django aleatorio sin mostrarlo; los otros scripts rechazan ejemplos o credenciales incompletas.

Firebase Admin usa una cuenta de servicio local y reglas que niegan acceso directo del cliente. La cuota reserva un ID en transacción, cuenta intentos, éxitos, fallos, bloqueos y excesos, y finaliza cada ID una sola vez. Migra números y la estructura antigua sin perder consumo; operaciones en proceso mayores a cinco minutos se marcan fallidas.

Los POST tienen CSRF, las plantillas conservan autoescape y los formularios validan. Los logs de Gemini registran únicamente clase y categoría. El filtro ganadero permite negativas seguras y bloquea dosis e instrucciones concretas.

El prototipo no tiene autenticación. La cookie firmada separa sesiones, pero un navegador compartido conserva el contexto. En producción se requieren HTTPS, `DJANGO_DEBUG=False`, rotación e IAM mínimo.

