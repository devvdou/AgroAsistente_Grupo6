from django import forms

from .constants import CULTIVOS, ESTADOS, REGIONES


class ContextoForm(forms.Form):
    region = forms.ChoiceField(label="Región de Chile", choices=REGIONES)
    predio = forms.CharField(label="Nombre del predio", min_length=2, max_length=80)
    modo = forms.ChoiceField(label="Tipo de producción", choices=[("Agrícola", "Agrícola"), ("Ganadera", "Ganadera")])
    cultivo = forms.ChoiceField(label="Cultivo", choices=[("", "Seleccione")] + CULTIVOS, required=False)
    superficie_m2 = forms.DecimalField(label="Superficie en m²", min_value=0.01, max_digits=12, decimal_places=2, required=False)

    def clean(self):
        data = super().clean()
        if data.get("modo") == "Agrícola":
            if not data.get("cultivo"):
                self.add_error("cultivo", "Selecciona un cultivo.")
            if data.get("superficie_m2") is None:
                self.add_error("superficie_m2", "Ingresa una superficie mayor que cero.")
        else:
            data["cultivo"] = "no_aplica"
            data["superficie_m2"] = data.get("superficie_m2") or 0
        return data


class ConsultaForm(forms.Form):
    pregunta = forms.CharField(
        label="Pregunta",
        min_length=10,
        max_length=300,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Ejemplo: ¿Qué debo observar antes de regar esta semana?"}),
        error_messages={"required": "Escribe una pregunta.", "min_length": "La pregunta debe tener al menos 10 caracteres.", "max_length": "La pregunta no puede superar 300 caracteres."},
    )


class LaborForm(forms.Form):
    titulo = forms.CharField(label="Labor", min_length=2, max_length=80)
    fecha = forms.DateField(label="Fecha", widget=forms.DateInput(attrs={"type": "date"}))


class EstadoLaborForm(forms.Form):
    labor_id = forms.CharField(widget=forms.HiddenInput)
    estado = forms.ChoiceField(choices=[(e, e) for e in ESTADOS])


class EstimacionForm(forms.Form):
    superficie_m2 = forms.DecimalField(label="Superficie", min_value=0.0001, max_digits=12, decimal_places=4)
    dosis_kg_m2 = forms.DecimalField(label="Dosis", min_value=0.0001, max_digits=12, decimal_places=6)
    unidad = forms.ChoiceField(label="Unidad de la dosis", choices=[("kg/m²", "kg/m²")])
    origen_dosis = forms.CharField(label="Origen de la dosis", min_length=3, max_length=120, help_text="Ejemplo: etiqueta del producto o ficha técnica INIA")
