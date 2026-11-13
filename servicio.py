"""Servicio de sensores: hilo en segundo plano que, cada `intervalo` segundos,

  1. genera una medición por astronauta (simulador),
  2. la guarda en la base de datos,
  3. evalúa las reglas de alerta y registra los eventos nuevos.

Funciona independiente de la interfaz: todas las pantallas (y todos los
tripulantes conectados) leen los mismos datos de la base de datos.
"""
from __future__ import annotations

import logging
import threading

import db
from alertas import GestorAlertas
from simulador import SimuladorAstronauta

log = logging.getLogger("astromonitor.servicio")


class ServicioSensores:
    def __init__(self, intervalo: float = 1.0, enfriamiento_alertas: float = 30.0):
        self.intervalo = intervalo
        self.gestor = GestorAlertas(enfriamiento=enfriamiento_alertas)
        self._sims: dict[int, SimuladorAstronauta] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._hilo: threading.Thread | None = None

    # -- control del simulador (lo usa la interfaz) ---------------------------------
    def _sim(self, astro_id: int) -> SimuladorAstronauta:
        if astro_id not in self._sims:
            self._sims[astro_id] = SimuladorAstronauta(astro_id)
        return self._sims[astro_id]

    def escenario(self, astro_id: int) -> str:
        with self._lock:
            return self._sim(astro_id).escenario

    def set_escenario(self, astro_id: int, nombre: str) -> None:
        with self._lock:
            self._sim(astro_id).set_escenario(nombre)

    # -- ciclo de vida --------------------------------------------------------------
    def tick(self) -> None:
        """Un ciclo completo: medir, guardar y alertar (útil también en pruebas)."""
        for a in db.listar_astronautas():
            with self._lock:
                med = self._sim(a["id"]).generar()
            db.insertar_medicion(a["id"], med)
            for alerta in self.gestor.nuevas(a["id"], med):
                db.insertar_evento(a["id"], alerta["severidad"], alerta["parametro"],
                                   alerta["valor"], alerta["mensaje"])

    def _bucle(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception:  # el hilo nunca debe morir por un error puntual
                log.exception("Error en el ciclo de sensores")
            self._stop.wait(self.intervalo)

    def iniciar(self) -> None:
        if self._hilo and self._hilo.is_alive():
            return
        self._stop.clear()
        self._hilo = threading.Thread(target=self._bucle, daemon=True, name="sensores")
        self._hilo.start()

    def detener(self) -> None:
        self._stop.set()
