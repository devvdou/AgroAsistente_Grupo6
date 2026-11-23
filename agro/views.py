import logging
import uuid
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import redirect, render

from .constants import CULTIVOS, REGION_NOMBRES
from .forms import ConsultaForm, ContextoForm, EstadoLaborForm, EstimacionForm, LaborForm
from .services import firebase_service
from .services.estimacion_service import calcular_cantidad
from .services.firebase_service import FirebaseNoDisponible
from .services.orientation_provider import generar_orientacion
from .services.weather_service import PronosticoNoDisponible, obtener_pronostico

logger = logging.getLogger(__name__)
CULTIVO_NOMBRES = dict(CULTIVOS)


def _session_id(request):
    if "visitante_id" not in request.session:
        request.session["visitante_id"] = uuid.uuid4().hex
    return request.session["visitante_id"]


def _contexto(request):
    return request.session.get("contexto")


def _base(request, **extra):
    contexto = _contexto(request)
    consumo = None
    try:
        consumo = firebase_service.obtener_consumo()
        consumo['limite'] = max(1, int(__import__('os').getenv('AI_DAILY_LIMIT', '20')))
    except Exception:
        pass
    return {"contexto": contexto, "consumo": consumo, **extra}


def inicio(request):
    _session_id(request)
    inicial = _contexto(request) or {}
    form = ContextoForm(initial=inicial)
    return render(request, "agro/inicio.html", _base(request, form=form))


def configurar_contexto(request):
    if request.method != "POST":
        return redirect("agro:inicio")
    form = ContextoForm(request.POST)
    if not form.is_valid():
        return render(request, "agro/inicio.html", _base(request, form=form), status=400)
    data = form.cleaned_data
    contexto = {
        "id": uuid.uuid4().hex,
        "region": data["region"],
        "region_nombre": REGION_NOMBRES[data["region"]],
        "predio": data["predio"].strip(),
        "modo": data["modo"],
        "cultivo": data["cultivo"],
        "cultivo_nombre": CULTIVO_NOMBRES.get(data["cultivo"], "No aplica"),
        "superficie_m2": str(data["superficie_m2"]),
    }
    request.session["contexto"] = contexto
    try:
        firebase_service.guardar_contexto(_session_id(request), contexto)
        messages.success(request, "Contexto guardado en Firebase.")
    except FirebaseNoDisponible:
        logger.warning("Firebase no disponible al guardar contexto")
        messages.warning(request, "El contexto quedó activo en esta sesión, pero Firebase no está disponible para persistirlo.")
    return redirect("agro:consulta")


def consulta(request):
    contexto = _contexto(request)
    if not contexto:
        messages.info(request, "Configura el contexto antes de realizar una consulta.")
        return redirect("agro:inicio")
    form = ConsultaForm(request.POST or None)
    resultado = pronostico = None
    error_pronostico = ""
    if request.method == "POST" and form.is_valid():
        pregunta = form.cleaned_data["pregunta"]
        try:
            resultado = generar_orientacion(contexto, pregunta)
        except Exception:
            logger.exception("Error controlado al generar orientación")
            messages.error(request, "No fue posible generar una orientación en este momento.")
        try:
            pronostico = obtener_pronostico(contexto["region"])
        except PronosticoNoDisponible:
            error_pronostico = "El pronóstico de Open-Meteo no está disponible en este momento."
    status = 400 if request.method == "POST" and not form.is_valid() else 200
    return render(request, "agro/consulta.html", _base(request, form=form, resultado=resultado, pronostico=pronostico, error_pronostico=error_pronostico), status=status)


def labores(request):
    contexto = _contexto(request)
    if not contexto:
        messages.info(request, "Configura el contexto antes de gestionar labores.")
        return redirect("agro:inicio")
    form = LaborForm()
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "crear":
            form = LaborForm(request.POST)
            if form.is_valid():
                labor = {"titulo": form.cleaned_data["titulo"].strip(), "fecha": form.cleaned_data["fecha"].isoformat(), "estado": "Pendiente"}
                try:
                    firebase_service.crear_labor(_session_id(request), contexto["id"], labor)
                    messages.success(request, "Labor agregada.")
                    return redirect("agro:labores")
                except FirebaseNoDisponible:
                    messages.error(request, "No fue posible guardar la labor porque Firebase no está disponible.")
        elif accion == "estado":
            estado_form = EstadoLaborForm(request.POST)
            if estado_form.is_valid():
                try:
                    firebase_service.cambiar_estado_labor(_session_id(request), contexto["id"], estado_form.cleaned_data["labor_id"], estado_form.cleaned_data["estado"])
                    messages.success(request, "Estado actualizado.")
                    return redirect("agro:labores")
                except FirebaseNoDisponible:
                    messages.error(request, "No fue posible actualizar la labor.")
    try:
        lista = firebase_service.listar_labores(_session_id(request), contexto["id"])
    except FirebaseNoDisponible:
        lista = []
        messages.warning(request, "No fue posible cargar las labores desde Firebase.")
    status = 400 if request.method == "POST" and form.errors else 200
    return render(request, "agro/labores.html", _base(request, form=form, labores=lista), status=status)


def estimacion(request):
    contexto = _contexto(request)
    initial = {}
    if contexto and Decimal(contexto.get("superficie_m2", "0")) > 0:
        initial["superficie_m2"] = contexto["superficie_m2"]
    form = EstimacionForm(request.POST or None, initial=initial)
    resultado = None
    if request.method == "POST" and form.is_valid():
        cantidad = calcular_cantidad(form.cleaned_data["superficie_m2"], form.cleaned_data["dosis_kg_m2"])
        resultado = {**form.cleaned_data, "cantidad": cantidad.quantize(Decimal("0.001"))}
    status = 400 if request.method == "POST" and not form.is_valid() else 200
    return render(request, "agro/estimacion.html", _base(request, form=form, resultado=resultado), status=status)
