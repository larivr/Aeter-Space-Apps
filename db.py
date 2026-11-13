"""Capa de datos del proyecto (SQLite).

Tablas:
  astronautas -> ficha médica de cada tripulante
  mediciones  -> serie temporal de signos vitales
  eventos     -> alertas generadas por el sistema (y su reconocimiento)
  notas       -> notas clínicas / bitácora médica

Cada función abre y cierra su propia conexión, así que es seguro usarla desde
varios hilos (el servicio de sensores) y desde la interfaz a la vez.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

VITALES = ("fc", "pas", "pad", "spo2", "temp", "fr")

SCHEMA = """
CREATE TABLE IF NOT EXISTS astronautas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    rol          TEXT,
    edad         INTEGER,
    peso_kg      REAL,
    tipo_sangre  TEXT,
    alergias     TEXT DEFAULT '',
    medicamentos TEXT DEFAULT '',
    condiciones  TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS mediciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    astronauta_id INTEGER NOT NULL REFERENCES astronautas(id),
    ts            TEXT NOT NULL,
    fc            REAL,   -- frecuencia cardíaca (lpm)
    pas           REAL,   -- presión sistólica (mmHg)
    pad           REAL,   -- presión diastólica (mmHg)
    spo2          REAL,   -- saturación de oxígeno (%)
    temp          REAL,   -- temperatura (°C)
    fr            REAL    -- frecuencia respiratoria (rpm)
);
CREATE INDEX IF NOT EXISTS idx_med_astro_id ON mediciones (astronauta_id, id);
CREATE INDEX IF NOT EXISTS idx_med_astro_ts ON mediciones (astronauta_id, ts);

CREATE TABLE IF NOT EXISTS eventos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    astronauta_id  INTEGER NOT NULL REFERENCES astronautas(id),
    ts             TEXT NOT NULL,
    severidad      TEXT NOT NULL,      -- 'advertencia' | 'critica'
    parametro      TEXT NOT NULL,
    valor          REAL,
    mensaje        TEXT NOT NULL,
    reconocida     INTEGER NOT NULL DEFAULT 0,
    reconocida_por TEXT,
    reconocida_ts  TEXT
);
CREATE INDEX IF NOT EXISTS idx_evt_astro ON eventos (astronauta_id, id);

CREATE TABLE IF NOT EXISTS notas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    astronauta_id INTEGER NOT NULL REFERENCES astronautas(id),
    ts            TEXT NOT NULL,
    autor         TEXT,
    nota          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nota_astro ON notas (astronauta_id, id);
"""

# Tripulación FICTICIA para la demo.
TRIPULACION = [
    dict(nombre="Ana Rojas", rol="Comandante", edad=41, peso_kg=63, tipo_sangre="O+",
         alergias="Ninguna conocida", medicamentos="Ninguno",
         condiciones="Sin antecedentes relevantes"),
    dict(nombre="Luis Vargas", rol="Ingeniero de vuelo", edad=36, peso_kg=78, tipo_sangre="A+",
         alergias="Penicilina", medicamentos="Ninguno",
         condiciones="Asma leve en la infancia"),
    dict(nombre="Sofía Chaves", rol="Oficial médico", edad=38, peso_kg=58, tipo_sangre="B+",
         alergias="Ibuprofeno (molestias gástricas)", medicamentos="Antihistamínico estacional",
         condiciones="Rinitis alérgica"),
    dict(nombre="Marco Jiménez", rol="Especialista de misión", edad=45, peso_kg=84,
         tipo_sangre="AB-", alergias="Ninguna conocida", medicamentos="Ninguno",
         condiciones="Hipertensión leve controlada"),
]

CAMPOS_EDITABLES = ("peso_kg", "tipo_sangre", "alergias", "medicamentos", "condiciones")


def _ruta_db() -> Path:
    return Path(os.environ.get("ASTRO_DB") or Path(__file__).with_name("astromonitor.db"))


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def conexion():
    con = sqlite3.connect(_ruta_db(), timeout=15)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with conexion() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)


def sembrar_astronautas() -> None:
    """Inserta la tripulación de ejemplo si la tabla está vacía."""
    with conexion() as con:
        if con.execute("SELECT COUNT(*) FROM astronautas").fetchone()[0] > 0:
            return
        for a in TRIPULACION:
            con.execute(
                "INSERT INTO astronautas (nombre, rol, edad, peso_kg, tipo_sangre, alergias,"
                " medicamentos, condiciones) VALUES (:nombre, :rol, :edad, :peso_kg,"
                " :tipo_sangre, :alergias, :medicamentos, :condiciones)",
                a,
            )


# --------------------------------------------------------------------------- astronautas
def listar_astronautas() -> list[dict]:
    with conexion() as con:
        return [dict(f) for f in con.execute("SELECT * FROM astronautas ORDER BY id")]


def obtener_astronauta(astro_id: int) -> dict | None:
    with conexion() as con:
        fila = con.execute("SELECT * FROM astronautas WHERE id=?", (astro_id,)).fetchone()
    return dict(fila) if fila else None


def actualizar_astronauta(astro_id: int, **campos) -> None:
    campos = {k: v for k, v in campos.items() if k in CAMPOS_EDITABLES}
    if not campos:
        return
    asignaciones = ", ".join(f"{k}=?" for k in campos)
    with conexion() as con:
        con.execute(f"UPDATE astronautas SET {asignaciones} WHERE id=?",
                    (*campos.values(), astro_id))


# --------------------------------------------------------------------------- mediciones
def insertar_medicion(astro_id: int, med: dict) -> None:
    with conexion() as con:
        con.execute(
            "INSERT INTO mediciones (astronauta_id, ts, fc, pas, pad, spo2, temp, fr)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (astro_id, ahora(), *(med[v] for v in VITALES)),
        )


def ultimas_mediciones(astro_id: int, n: int = 100) -> list[dict]:
    """Las últimas n mediciones, en orden cronológico (la más reciente al final)."""
    with conexion() as con:
        filas = con.execute(
            "SELECT * FROM mediciones WHERE astronauta_id=? ORDER BY id DESC LIMIT ?",
            (astro_id, n),
        ).fetchall()
    return [dict(f) for f in reversed(filas)]


def ultima_medicion(astro_id: int) -> dict | None:
    recientes = ultimas_mediciones(astro_id, 1)
    return recientes[0] if recientes else None


def mediciones(astro_id: int, desde: str | None = None, max_puntos: int | None = 2000) -> list[dict]:
    """Mediciones desde una fecha ISO, reduciendo la cantidad a ~max_puntos para graficar."""
    cond, params = "astronauta_id=?", [astro_id]
    if desde:
        cond += " AND ts>=?"
        params.append(desde)
    with conexion() as con:
        total = con.execute(f"SELECT COUNT(*) FROM mediciones WHERE {cond}", params).fetchone()[0]
        salto = max(1, total // max_puntos) if max_puntos else 1
        filas = con.execute(
            f"SELECT * FROM mediciones WHERE {cond} AND (id % ?) = 0 ORDER BY id",
            (*params, salto),
        ).fetchall()
    return [dict(f) for f in filas]


def todas_mediciones(astro_id: int) -> list[dict]:
    with conexion() as con:
        filas = con.execute(
            "SELECT * FROM mediciones WHERE astronauta_id=? ORDER BY id", (astro_id,)
        ).fetchall()
    return [dict(f) for f in filas]


def resumen_mediciones(astro_id: int, desde: str | None = None) -> dict:
    """Mínimo / promedio / máximo de cada signo vital (y número de muestras)."""
    cond, params = "astronauta_id=?", [astro_id]
    if desde:
        cond += " AND ts>=?"
        params.append(desde)
    columnas = ", ".join(
        f"MIN({v}) AS {v}_min, AVG({v}) AS {v}_prom, MAX({v}) AS {v}_max" for v in VITALES
    )
    with conexion() as con:
        fila = con.execute(
            f"SELECT COUNT(*) AS n, {columnas} FROM mediciones WHERE {cond}", params
        ).fetchone()
    return dict(fila)


# --------------------------------------------------------------------------- eventos
def insertar_evento(astro_id: int, severidad: str, parametro: str, valor: float, mensaje: str) -> None:
    with conexion() as con:
        con.execute(
            "INSERT INTO eventos (astronauta_id, ts, severidad, parametro, valor, mensaje)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (astro_id, ahora(), severidad, parametro, valor, mensaje),
        )


def listar_eventos(astro_id: int | None = None, limite: int = 100,
                   solo_pendientes: bool = False) -> list[dict]:
    sql = ("SELECT e.*, a.nombre AS astronauta FROM eventos e"
           " JOIN astronautas a ON a.id = e.astronauta_id WHERE 1=1")
    params: list = []
    if astro_id is not None:
        sql += " AND e.astronauta_id=?"
        params.append(astro_id)
    if solo_pendientes:
        sql += " AND e.reconocida=0"
    sql += " ORDER BY e.id DESC LIMIT ?"
    params.append(limite)
    with conexion() as con:
        return [dict(f) for f in con.execute(sql, params)]


def eventos_desde(ultimo_id: int) -> list[dict]:
    """Eventos con id mayor a ultimo_id, en orden cronológico."""
    with conexion() as con:
        filas = con.execute(
            "SELECT e.*, a.nombre AS astronauta FROM eventos e"
            " JOIN astronautas a ON a.id = e.astronauta_id WHERE e.id>? ORDER BY e.id",
            (ultimo_id,),
        ).fetchall()
    return [dict(f) for f in filas]


def ultimo_evento_id() -> int:
    with conexion() as con:
        return con.execute("SELECT COALESCE(MAX(id), 0) FROM eventos").fetchone()[0]


def reconocer_eventos(por: str, astro_id: int | None = None) -> None:
    sql = "UPDATE eventos SET reconocida=1, reconocida_por=?, reconocida_ts=? WHERE reconocida=0"
    params: list = [por, ahora()]
    if astro_id is not None:
        sql += " AND astronauta_id=?"
        params.append(astro_id)
    with conexion() as con:
        con.execute(sql, params)


# --------------------------------------------------------------------------- notas clínicas
def insertar_nota(astro_id: int, autor: str, nota: str) -> None:
    with conexion() as con:
        con.execute(
            "INSERT INTO notas (astronauta_id, ts, autor, nota) VALUES (?, ?, ?, ?)",
            (astro_id, ahora(), autor, nota),
        )


def listar_notas(astro_id: int, limite: int = 50) -> list[dict]:
    with conexion() as con:
        filas = con.execute(
            "SELECT * FROM notas WHERE astronauta_id=? ORDER BY id DESC LIMIT ?",
            (astro_id, limite),
        ).fetchall()
    return [dict(f) for f in filas]
