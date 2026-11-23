"""Transformaciones puras del contador; Firebase aplica cada una en transacción."""
from copy import deepcopy


def normalizar(actual, ahora):
    if isinstance(actual, (int, float)):
        actual = {'exitosas': max(0, int(actual))}
    data = deepcopy(actual) if isinstance(actual, dict) else {}
    for campo in ('exitosas', 'fallidas', 'bloqueadas', 'excesos'):
        data[campo] = max(0, int(data.get(campo, 0)))
    pendientes_antiguos = max(0, int(data.pop('reservadas', 0)))
    if 'intentos' not in data:
        data['intentos'] = sum(data[c] for c in ('exitosas', 'fallidas', 'bloqueadas')) + pendientes_antiguos
        data['fallidas'] += pendientes_antiguos
        data['abandonadas_legacy'] = pendientes_antiguos
    data.setdefault('operaciones', {})
    for op in data['operaciones'].values():
        if op.get('estado') == 'en_proceso' and ahora - op.get('inicio', 0) > 300:
            op.update(estado='fallida', fin=ahora, motivo='abandonada')
            data['fallidas'] += 1
    data['version'] = 2
    return data


def iniciar(actual, identificador, limite, ahora):
    data = normalizar(actual, ahora)
    if identificador in data['operaciones']:
        return data
    if data['intentos'] >= limite:
        data['excesos'] += 1
        data['operaciones'][identificador] = {'estado': 'rechazada', 'inicio': ahora}
    else:
        data['intentos'] += 1
        data['operaciones'][identificador] = {'estado': 'en_proceso', 'inicio': ahora}
    return data


def finalizar(actual, identificador, estado, ahora):
    if estado not in ('exitosa', 'fallida', 'bloqueada'):
        raise ValueError('Estado de cuota inválido')
    data = normalizar(actual, ahora)
    op = data['operaciones'].get(identificador)
    if op and op['estado'] == 'en_proceso':
        op.update(estado=estado, fin=ahora)
        data[{'exitosa': 'exitosas', 'fallida': 'fallidas', 'bloqueada': 'bloqueadas'}[estado]] += 1
    return data
