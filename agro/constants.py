REGIONES = [
    ("arica", "Arica y Parinacota"),
    ("tarapaca", "Tarapacá"),
    ("antofagasta", "Antofagasta"),
    ("atacama", "Atacama"),
    ("coquimbo", "Coquimbo"),
    ("valparaiso", "Valparaíso"),
    ("metropolitana", "Metropolitana de Santiago"),
    ("ohiggins", "Libertador General Bernardo O’Higgins"),
    ("maule", "Maule"),
    ("nuble", "Ñuble"),
    ("biobio", "Biobío"),
    ("araucania", "La Araucanía"),
    ("los_rios", "Los Ríos"),
    ("los_lagos", "Los Lagos"),
    ("aysen", "Aysén del General Carlos Ibáñez del Campo"),
    ("magallanes", "Magallanes y de la Antártica Chilena"),
]

REGION_NOMBRES = dict(REGIONES)
COORDENADAS_REGION = {
    "arica": ("Arica", -18.48, -70.31),
    "tarapaca": ("Iquique", -20.21, -70.15),
    "antofagasta": ("Antofagasta", -23.65, -70.40),
    "atacama": ("Copiapó", -27.37, -70.33),
    "coquimbo": ("La Serena", -29.90, -71.25),
    "valparaiso": ("Valparaíso", -33.05, -71.62),
    "metropolitana": ("Santiago", -33.45, -70.67),
    "ohiggins": ("Rancagua", -34.17, -70.74),
    "maule": ("Talca", -35.43, -71.66),
    "nuble": ("Chillán", -36.61, -72.10),
    "biobio": ("Concepción", -36.83, -73.05),
    "araucania": ("Temuco", -38.74, -72.60),
    "los_rios": ("Valdivia", -39.82, -73.25),
    "los_lagos": ("Puerto Montt", -41.47, -72.94),
    "aysen": ("Coyhaique", -45.57, -72.07),
    "magallanes": ("Punta Arenas", -53.16, -70.91),
}

CULTIVOS = [(x.lower(), x) for x in ["Tomate", "Maíz", "Papa", "Trigo", "Avena", "Cebolla", "Lechuga", "Otro"]]
ESTADOS = ["Pendiente", "En curso", "Hecha"]
