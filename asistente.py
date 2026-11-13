
from __future__ import annotations

import os
import re
import time
from typing import Iterator

import alertas as mod_alertas
import protocolos

MODELO = os.environ.get("ASTRO_MODELO", "claude-sonnet-5-5")

SYSTEM_BASE = """Eres ASTRA, el asistente médico de a bordo de una tripulación de astronautas.
Apoyas al oficial médico y a la tripulación.
Reglas:
- Responde siempre en español, claro y breve. En emergencias: pasos cortos y faciles de entender, empezando por la acción más urgente.
- Ten en cuenta que están en  lejos de la Tierra y la coomunicación con retraso puede tener retraso.
- Usa solo los signos vitales, ficha médica y alertas del estado actual. No inventar datos.
- Antes de recomendar cualquier medicamento, revisar alergias, medicamentos actuales y antecedentes del paciente y menciónalos explícitamente.
- Indica usar la dosis de la etiqueta del botiquín o del protocolo de la misión, confirmada por el oficial médico o el cirujano de vuelo.
- Basa tus respuestas en los protocolos de emergencia. Si algo no está cubierto, dilo y recomienda consultar al cirujano de vuelo / Control de Misión.
- No diagnostiques con certeza: habla de posibles causas.
- Si hay riesgo vital indica en orden: 1) alertar a la tripulación, 2) la acción inmediata, 3) contactar al cirujano de vuelo.
- Cierra las respuestas de emergencia con qué medir de nuevo y cuándo."""


def construir_contexto(astronauta: dict, recientes: list[dict], alertas_activas: list[dict],
                       notas: list[dict] | None = None) -> str:
    a = astronauta
    lineas = [
        "## Paciente",
        f"- Nombre: {a['nombre']} ({a['rol']})",
        f"- Edad: {a['edad']} años · Peso: {a['peso_kg']} kg · Grupo sanguíneo: {a['tipo_sangre']}",
        f"- ALERGIAS: {a['alergias'] or 'no registradas'}",
        f"- Medicamentos actuales: {a['medicamentos'] or 'ninguno'}",
        f"- Antecedentes: {a['condiciones'] or 'ninguno'}",
    ]
    if recientes:
        ult, ini = recientes[-1], recientes[0]
        lineas.append(f"\n## Signos vitales actuales (hora {ult['ts'][11:19]})")
        for p in mod_alertas.ORDEN:
            u = mod_alertas.UMBRALES[p]
            tendencia = ""
            if len(recientes) > 1 and ini[p] != ult[p]:
                tendencia = (f"  [tendencia: {mod_alertas.formatear(p, ini[p])} -> "
                             f"{mod_alertas.formatear(p, ult[p])} en las últimas {len(recientes)} muestras]")
            lineas.append(f"- {u['nombre']}: {mod_alertas.formatear(p, ult[p])}{tendencia}")
    else:
        lineas.append("\n## Signos vitales: sin datos todavía")

    lineas.append("\n## Alertas activas")
    if alertas_activas:
        for al in alertas_activas:
            lineas.append(f"- [{al['severidad'].upper()}] {al['mensaje']}")
    else:
        lineas.append("- Ninguna: todos los signos dentro del rango normal.")

    if notas:
        lineas.append("\n## Últimas notas clínicas")
        for n in notas[:3]:
            lineas.append(f"- {n['ts'][:16]} ({n['autor']}): {n['nota']}")
    return "\n".join(lineas)


def construir_system(contexto: str) -> str:
    return (f"{SYSTEM_BASE}\n\n# PROTOCOLOS DE REFERENCIA\n{protocolos.texto_referencia()}"
            f"\n\n# CONTEXTO ACTUAL\n{contexto}")


def _mensajes_validos(historial: list[dict], maximo: int = 12) -> list[dict]:
    """Últimos mensajes, empezando por uno del usuario (requisito de la API)."""
    msgs = [{"role": m["role"], "content": m["content"]} for m in historial[-maximo:]]
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    return msgs


def _stream_texto(texto: str, pausa: float = 0.01) -> Iterator[str]:
    for token in re.findall(r"\S+\s*", texto):
        yield token
        time.sleep(pausa)


# --------------------------------------------------------------------------- modo offline
def respuesta_offline(pregunta: str, astronauta: dict, alertas_activas: list[dict]) -> str:
    q = protocolos.normalizar(pregunta)
    partes: list[str] = []

    quiere_medir = bool(re.search(r"\b(medir|mido|medicion|mediciones|tomar|tomo|mide|se mide)\b", q))
    pide_guia = any(p in q for p in ("emergencia", "guia", "guiame", "que hago", "ayuda",
                                      "urgente", "paso a paso", "situacion actual", "actual"))

    if alertas_activas:
        resumen = "; ".join(a["mensaje"] for a in alertas_activas)
        partes.append(f" **Estado actual de {astronauta['nombre']}:** {resumen}.\n"
                      "**Primero: avisa a la tripulación.**")

    if protocolos.detectar(q, {"med": protocolos.MEDICAMENTOS}):
        partes.append(f"**Ficha de {astronauta['nombre']}** · Alergias: {astronauta['alergias'] or 'no registradas'} · "
                      f"Medicamentos actuales: {astronauta['medicamentos'] or 'ninguno'} · "
                      f"Antecedentes: {astronauta['condiciones'] or 'ninguno'}")
        partes.append(protocolos.medicamentos_md())
    elif quiere_medir:
        claves = protocolos.detectar(q, protocolos.MEDICIONES)
        if claves:
            partes.extend(protocolos.medicion_md(c) for c in claves)
        else:
            opciones = ", ".join(m["titulo"].replace("Cómo medir ", "") for m in protocolos.MEDICIONES.values())
            partes.append(f"Puedo guiarte para medir: {opciones}. ¿Cuál necesitas?")
    else:
        claves = protocolos.detectar(q, protocolos.EMERGENCIAS)
        if pide_guia and alertas_activas:
            claves = protocolos.protocolos_para_alertas(alertas_activas)
        elif not claves and alertas_activas:
            claves = protocolos.protocolos_para_alertas(alertas_activas)
        if claves:
            partes.extend(protocolos.emergencia_md(c) for c in claves)
        elif not alertas_activas:
            partes.append(
                "No hay alertas activas y no reconozco la consulta. Puedo ayudarte con:\n"
                "- Cómo medir presión, SpO₂, pulso, temperatura o respiración\n"
                "- Guías para hipoxia, taquicardia/bradicardia, hipertensión/hipotensión, fiebre o hipotermia\n"
                "- Uso seguro de medicamentos del botiquín"
            )

    partes.append("_Modo offline: respuesta basada en los protocolos locales de la aplicación. "
                  "Confirma con el oficial médico / cirujano de vuelo._")
    return "\n\n".join(partes)


# --------------------------------------------------------------------------- función principal
def responder_stream(historial: list[dict], astronauta: dict, recientes: list[dict],
                     alertas_activas: list[dict], notas: list[dict] | None = None,
                     api_key: str | None = None) -> Iterator[str]:
    """Genera la respuesta del asistente en trozos de texto."""
    pregunta = historial[-1]["content"] if historial else ""
    clave = (api_key or os.environ.get("ANTHROPIC_API_KEY") or "").strip()

    if clave:
        try:
            import anthropic

            cliente = anthropic.Anthropic(api_key=clave)
            system = construir_system(construir_contexto(astronauta, recientes, alertas_activas, notas))
            with cliente.messages.stream(
                model=MODELO,
                max_tokens=1000,
                system=system,
                messages=_mensajes_validos(historial),
            ) as stream:
                for texto in stream.text_stream:
                    yield texto
            return
        except Exception as e:  # sin internet, key inválida, límite de uso...
            yield f"No pude contactar a la IA ({type(e).__name__}). Respondo en modo offline.\n\n"

    yield from _stream_texto(respuesta_offline(pregunta, astronauta, alertas_activas))
