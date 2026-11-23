from django.urls import path

from . import views

app_name = "agro"
urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("contexto/", views.configurar_contexto, name="contexto"),
    path("consulta/", views.consulta, name="consulta"),
    path("labores/", views.labores, name="labores"),
    path("estimacion/", views.estimacion, name="estimacion"),
]
