import requests

from agro.constants import COORDENADAS_REGION


class PronosticoNoDisponible(Exception):
    pass


def obtener_pronostico(region):
    if region not in COORDENADAS_REGION:
        raise PronosticoNoDisponible("Región no válida")
    localidad, latitud, longitud = COORDENADAS_REGION[region]
    try:
        respuesta = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitud,
                "longitude": longitud,
                "forecast_days": 3,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "current": "temperature_2m",
                "timezone": "America/Santiago",
            },
            timeout=8,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        diario = datos.get("daily", {})
        fechas = diario.get("time", [])
        minimas = diario.get("temperature_2m_min", [])
        maximas = diario.get("temperature_2m_max", [])
        precipitaciones = diario.get("precipitation_sum", [])
        actualizado = datos.get("current", {}).get("time")
        if not fechas or not (len(fechas) == len(minimas) == len(maximas) == len(precipitaciones)):
            raise ValueError("Respuesta meteorológica incompleta")
        if not actualizado:
            raise ValueError("Hora de actualización ausente")
        return {
            "localidad": localidad,
            "latitud": latitud,
            "longitud": longitud,
            "actualizado": actualizado.replace("T", " "),
            "dias": [
                {"fecha": fechas[i], "minima": minimas[i], "maxima": maximas[i], "precipitacion": precipitaciones[i]}
                for i in range(len(fechas))
            ],
            "fuente": "Open-Meteo",
        }
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise PronosticoNoDisponible("El pronóstico no está disponible en este momento") from exc
