"""Generador de datos: simula los sensores de un astronauta.

Idea: cada signo vital es un número que "flota" alrededor de un valor objetivo.
En cada tick (1 segundo) hacemos dos cosas:

    valor_nuevo = valor + velocidad * (objetivo - valor)   # se acerca al objetivo
                        + ruido_aleatorio                  # pequeño temblor natural

* En estado normal el objetivo es el valor base de la persona (reposo).
* Al activar un ESCENARIO (hipoxia, taquicardia...) el objetivo de algunos signos
  cambia (p. ej. SpO2 -> 80) y los valores "caen" hacia ahí de forma gradual,
  como pasaría en una emergencia real.
* Al volver a "normal" el objetivo regresa al valor base y el paciente se recupera.

Uso:
    sim = SimuladorAstronauta(astro_id=1)
    sim.generar()                     # -> {'fc': 66, 'pas': 118, 'pad': 74, 'spo2': 98, ...}
    sim.set_escenario("hipoxia")      # a partir de aquí los valores empiezan a empeorar
    sim.generar()
    sim.set_escenario("normal")       # recuperación

Para ver una demostración en la terminal:   python simulador.py

Para usar sensores REALES basta con reemplazar `generar()` por una función que lea
tus dispositivos y devuelva el mismo diccionario (fc, pas, pad, spo2, temp, fr).
"""
from __future__ import annotations

import random

VITALES = ("fc", "pas", "pad", "spo2", "temp", "fr")

# Valores hacia los que tiende cada escenario (solo los signos que cambian).
ESCENARIOS: dict[str, dict[str, float]] = {
    "normal": {},
    "hipoxia": {"spo2": 80, "fc": 120, "fr": 27},
    "taquicardia": {"fc": 155},
    "hipertension": {"pas": 190, "pad": 115, "fc": 100},
    "hipotension": {"pas": 78, "pad": 48, "fc": 122},
    "fiebre": {"temp": 39.4, "fc": 112, "fr": 21},
}

ETIQUETAS_ESCENARIO = {
    "normal": "✅ Normal (reposo)",
    "hipoxia": "🫁 Hipoxia (SpO₂ baja)",
    "taquicardia": "💓 Taquicardia",
    "hipertension": "🩸 Hipertensión",
    "hipotension": "📉 Hipotensión / shock",
    "fiebre": "🌡️ Fiebre",
}

# Desviación del "temblor" aleatorio de cada signo en cada tick.
RUIDO = {"fc": 1.2, "pas": 1.5, "pad": 1.2, "spo2": 0.25, "temp": 0.04, "fr": 0.3}

# Rango físicamente posible (para que la simulación nunca produzca valores absurdos).
LIMITES = {"fc": (30, 220), "pas": (50, 260), "pad": (30, 150),
           "spo2": (60, 100), "temp": (33, 42), "fr": (4, 45)}


class SimuladorAstronauta:
    def __init__(self, astro_id: int = 0, velocidad: float = 0.12):
        """velocidad: 0-1, qué tan rápido se acerca al objetivo (0.12 ≈ 15-20 s)."""
        # Valores base distintos (pero repetibles) para cada astronauta.
        r = random.Random(1000 + astro_id)
        self.base = {
            "fc": r.uniform(60, 74),
            "pas": r.uniform(112, 124),
            "pad": r.uniform(70, 78),
            "spo2": r.uniform(97.5, 99.0),
            "temp": r.uniform(36.5, 36.9),
            "fr": r.uniform(14, 17),
        }
        self.estado = dict(self.base)
        self.escenario = "normal"
        self.velocidad = velocidad
        self._rng = random.Random()

    def set_escenario(self, nombre: str) -> None:
        if nombre not in ESCENARIOS:
            raise ValueError(f"Escenario desconocido: {nombre!r}. Opciones: {list(ESCENARIOS)}")
        self.escenario = nombre

    def objetivo(self) -> dict[str, float]:
        return {**self.base, **ESCENARIOS[self.escenario]}

    def generar(self) -> dict[str, float]:
        """Avanza un tick y devuelve la medición actual."""
        objetivo = self.objetivo()
        med: dict[str, float] = {}
        for v in VITALES:
            x = self.estado[v]
            x += self.velocidad * (objetivo[v] - x) + self._rng.gauss(0, RUIDO[v])
            lo, hi = LIMITES[v]
            x = min(max(x, lo), hi)
            self.estado[v] = x
            med[v] = round(x, 1) if v == "temp" else int(round(x))
        return med


if __name__ == "__main__":
    from alertas import evaluar_medicion, nivel_global

    sim = SimuladorAstronauta(astro_id=1)
    plan = [("normal", 8), ("hipoxia", 25), ("normal", 25)]
    print(f"{'t':>3}  {'escenario':<9} {'FC':>4} {'PAS/PAD':>8} {'SpO2':>5} {'Temp':>5} {'FR':>3}  estado")
    t = 0
    for escenario, ticks in plan:
        sim.set_escenario(escenario)
        for _ in range(ticks):
            m = sim.generar()
            t += 1
            nivel = nivel_global(evaluar_medicion(m))
            print(f"{t:>3}  {escenario:<9} {m['fc']:>4} {m['pas']:>4}/{m['pad']:<3} "
                  f"{m['spo2']:>5} {m['temp']:>5} {m['fr']:>3}  {nivel}")
