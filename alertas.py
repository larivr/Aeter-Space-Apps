"""Reglas de alerta por umbral.

Cada signo vital tiene dos niveles:
  adv  -> advertencia (amarillo): fuera del rango normal
  crit -> crítica (rojo): peligro, acción inmediata
Un límite en None significa "sin límite por ese lado".

⚠ Umbrales de ejemplo para el prototipo. Deben ajustarse con criterio médico
(y según la persona y la actividad: ejercicio, EVA, reposo...).
"""
from __future__ import annotations

import time

ORDEN = ("fc", "pas", "pad", "spo2", "temp", "fr")

UMBRALES = {
    "fc":   {"nombre": "Frecuencia cardíaca",    "unidad": "lpm",  "adv": (50, 110),   "crit": (40, 130),   "decimales": 0},
    "pas":  {"nombre": "Presión sistólica",      "unidad": "mmHg", "adv": (100, 140), "crit": (85, 180),   "decimales": 0},
    "pad":  {"nombre": "Presión diastólica",     "unidad": "mmHg", "adv": (60, 90),    "crit": (50, 110),   "decimales": 0},
    "spo2": {"nombre": "Saturación de oxígeno",  "unidad": "%",    "adv": (94, None),  "crit": (90, None),  "decimales": 0},
    "temp": {"nombre": "Temperatura corporal",   "unidad": "°C",   "adv": (36.0, 37.8), "crit": (35.0, 39.0), "decimales": 1},
    "fr":   {"nombre": "Frecuencia respiratoria", "unidad": "rpm", "adv": (10, 20),    "crit": (8, 28),     "decimales": 0},
}


def formatear(param: str, valor: float) -> str:
    u = UMBRALES[param]
    return f"{valor:.{u['decimales']}f} {u['unidad']}"


def evaluar_medicion(med: dict) -> list[dict]:
    """Devuelve la lista de signos fuera de rango en una medición (función pura)."""
    resultado = []
    for p in ORDEN:
        valor = med.get(p)
        if valor is None:
            continue
        u = UMBRALES[p]
        lo_c, hi_c = u["crit"]
        lo_a, hi_a = u["adv"]
        sev = direccion = limite = None
        if lo_c is not None and valor < lo_c:
            sev, direccion, limite = "critica", "baja", lo_c
        elif hi_c is not None and valor > hi_c:
            sev, direccion, limite = "critica", "alta", hi_c
        elif lo_a is not None and valor < lo_a:
            sev, direccion, limite = "advertencia", "baja", lo_a
        elif hi_a is not None and valor > hi_a:
            sev, direccion, limite = "advertencia", "alta", hi_a
        if sev:
            prefijo = "críticamente " if sev == "critica" else ""
            resultado.append({
                "parametro": p,
                "nombre": u["nombre"],
                "valor": valor,
                "unidad": u["unidad"],
                "severidad": sev,
                "direccion": direccion,
                "limite": limite,
                "mensaje": f"{u['nombre']} {prefijo}{direccion}: {formatear(p, valor)} "
                           f"(límite {formatear(p, limite)})",
            })
    return resultado


def nivel_global(alertas: list[dict]) -> str:
    """'critica' | 'advertencia' | 'normal'."""
    if any(a["severidad"] == "critica" for a in alertas):
        return "critica"
    if alertas:
        return "advertencia"
    return "normal"


class GestorAlertas:
    """Evita spam: una misma alerta no se vuelve a registrar hasta pasado el
    `enfriamiento`, salvo que empeore (advertencia -> crítica). Si el signo
    vuelve a la normalidad unos segundos, la alerta se "rearma"."""

    def __init__(self, enfriamiento: float = 30.0, rearme: float = 10.0):
        self.enfriamiento = enfriamiento
        self.rearme = rearme
        self._ultimo: dict[tuple, tuple[str, float]] = {}
        self._normal_desde: dict[tuple, float] = {}

    def nuevas(self, astro_id: int, med: dict, ahora: float | None = None) -> list[dict]:
        ahora = time.monotonic() if ahora is None else ahora
        activas = {a["parametro"]: a for a in evaluar_medicion(med)}
        nuevas = []

        for p, a in activas.items():
            clave = (astro_id, p)
            self._normal_desde.pop(clave, None)
            previo = self._ultimo.get(clave)
            empeora = previo is not None and previo[0] == "advertencia" and a["severidad"] == "critica"
            if previo is None or empeora or ahora - previo[1] >= self.enfriamiento:
                self._ultimo[clave] = (a["severidad"], ahora)
                nuevas.append(a)

        for clave in [c for c in self._ultimo if c[0] == astro_id and c[1] not in activas]:
            desde = self._normal_desde.setdefault(clave, ahora)
            if ahora - desde >= self.rearme:
                del self._ultimo[clave]
                del self._normal_desde[clave]
        return nuevas
