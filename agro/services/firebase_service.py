import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import firebase_admin
from firebase_admin import credentials, db


class FirebaseNoDisponible(Exception):
    pass


class LimiteDiarioAlcanzado(Exception):
    pass


_lock = threading.Lock()


def _inicializar():
    if firebase_admin._apps:
        return
    database_url = os.getenv("FIREBASE_DATABASE_URL", "").strip()
    if not database_url:
        raise FirebaseNoDisponible("Configuración de Firebase incompleta")
    try:
        with _lock:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.ApplicationDefault(), {"databaseURL": database_url})
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible conectar con Firebase") from exc


def _ref(ruta):
    _inicializar()
    try:
        return db.reference(ruta)
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible acceder a Firebase") from exc


def guardar_contexto(session_id, contexto):
    try:
        _ref(f"sesiones/{session_id}/contexto").set(contexto)
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible guardar el contexto") from exc


def crear_labor(session_id, contexto_id, labor):
    try:
        return _ref(f"sesiones/{session_id}/predios/{contexto_id}/labores").push(labor).key
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible guardar la labor") from exc


def listar_labores(session_id, contexto_id):
    try:
        datos = _ref(f"sesiones/{session_id}/predios/{contexto_id}/labores").get() or {}
        labores = [{"id": key, **value} for key, value in datos.items() if isinstance(value, dict)]
        return sorted(labores, key=lambda item: (item.get("fecha", ""), item.get("titulo", "")))
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible leer las labores") from exc


def cambiar_estado_labor(session_id, contexto_id, labor_id, estado):
    try:
        _ref(f"sesiones/{session_id}/predios/{contexto_id}/labores/{labor_id}").update({"estado": estado})
    except FirebaseNoDisponible:
        raise
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible actualizar la labor") from exc


def fecha_chile():
    return datetime.now(ZoneInfo("America/Santiago")).date().isoformat()


def reservar_cuota(limite):
    import time
    import uuid
    from .quota_state import iniciar
    fecha = fecha_chile()
    identificador = uuid.uuid4().hex
    ahora = time.time()
    try:
        data = _ref(f"consumo_ia/{fecha}").transaction(
            lambda actual: iniciar(actual, identificador, limite, ahora)
        )
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible reservar la cuota") from exc
    if data['operaciones'][identificador]['estado'] == 'rechazada':
        raise LimiteDiarioAlcanzado
    return fecha, identificador


def finalizar_reserva(reserva, estado):
    import time
    from .quota_state import finalizar
    fecha, identificador = reserva
    ahora = time.time()
    try:
        _ref(f"consumo_ia/{fecha}").transaction(
            lambda actual: finalizar(actual, identificador, estado, ahora)
        )
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible finalizar la cuota") from exc


def confirmar_reserva(reserva, bloqueada=False):
    finalizar_reserva(reserva, 'bloqueada' if bloqueada else 'exitosa')


def liberar_reserva(reserva):
    finalizar_reserva(reserva, 'fallida')


def obtener_consumo():
    import time
    from .quota_state import normalizar
    ahora = time.time()
    try:
        return _ref(f"consumo_ia/{fecha_chile()}").transaction(
            lambda actual: normalizar(actual, ahora)
        )
    except Exception as exc:
        raise FirebaseNoDisponible("No fue posible consultar el consumo") from exc
