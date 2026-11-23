from decimal import Decimal


def calcular_cantidad(superficie_m2, dosis_kg_m2):
    superficie = Decimal(str(superficie_m2))
    dosis = Decimal(str(dosis_kg_m2))
    if superficie <= 0 or dosis <= 0:
        raise ValueError("La superficie y la dosis deben ser mayores que cero")
    return superficie * dosis
