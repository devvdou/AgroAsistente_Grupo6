# Decisión técnica de persistencia y arquitectura

## Decisión

El informe propuso Django y MariaDB. La aplicación final conserva Django para rutas, vistas, formularios, plantillas, validaciones y protección CSRF, pero sustituye MariaDB por Firebase Realtime Database para el prototipo académico solicitado.

Streamlit queda identificado como prototipo anterior y no forma parte de la aplicación final. No se incorporó la carpeta `legacy_streamlit` porque el único archivo útil fue auditado y su lógica necesaria quedó reimplementada sin copiar credenciales ni dependencias de la interfaz anterior.

## Consecuencias

Firebase permite una puesta en marcha rápida, operaciones atómicas mediante transacciones y una estructura simple para contextos, labores y consumo. Sus limitaciones son el acoplamiento a una plataforma externa, consultas menos expresivas que SQL, dependencia de conectividad y necesidad de diseñar cuidadosamente las rutas y reglas.

El Admin SDK se mantiene exclusivamente en el servidor Django. Ninguna credencial administrativa se envía al navegador. Las reglas de Realtime Database niegan el acceso directo del cliente, mientras IAM y las validaciones del servidor limitan las acciones administrativas.

Django usa sesiones firmadas en cookies y un backend de base de datos no operativo. Firebase es la persistencia de negocio.
