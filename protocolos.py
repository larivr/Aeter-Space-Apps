
from __future__ import annotations

import unicodedata

DESCARGO = (
    "Prototipo educativo de hackatón: no es un dispositivo médico ni sustituye al oficial "
    "médico, al cirujano de vuelo ni al Control de Misión. Datos y protocolos de ejemplo."
)


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar palabras clave."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# --------------------------------------------------------------------------- cómo medir
MEDICIONES = {
    "presion": {
        "titulo": "Cómo medir la presión arterial",
        "palabras": ["presion", "tension", "brazalete", "tensiometro", "arterial"],
        "pasos": [
            "Deja a la persona en reposo 5 minutos, sin hablar ni moverse; sujétala con las correas para que esté estable en microgravedad.",
            "Usa un brazalete del tamaño adecuado sobre el brazo desnudo, a la altura del corazón.",
            "Mantén el brazo relajado y apoyado. Inicia la medición y no hables mientras dura.",
            "Anota sistólica/diastólica y repite tras 1-2 minutos; registra el promedio.",
            "Si el valor es crítico, confirma con una segunda medición antes de actuar y avisa a la tripulación.",
        ],
    },
    "spo2": {
        "titulo": "Cómo medir la saturación de oxígeno (SpO₂)",
        "palabras": ["saturacion", "oximetro", "pulsioximetro", "spo2", "oxigeno"],
        "pasos": [
            "Retira esmalte o uñas postizas del dedo elegido y calienta la mano si está fría.",
            "Coloca el pulsioxímetro en el dedo índice o medio, con la mano relajada y sin moverla.",
            "Espera 20-30 segundos hasta que el valor se estabilice y la onda de pulso sea clara.",
            "Si el valor es bajo, cambia de dedo y repite: un sensor mal puesto da falsas alarmas.",
            "Anota el valor y la hora.",
        ],
    },
    "pulso": {
        "titulo": "Cómo medir el pulso (frecuencia cardíaca) manualmente",
        "palabras": ["pulso", "latidos", "frecuencia cardiaca", "cardiaca"],
        "pasos": [
            "Coloca dos dedos (índice y medio, nunca el pulgar) sobre la arteria radial: muñeca, lado del pulgar.",
            "Cuenta los latidos durante 30 segundos y multiplica por 2 (si es irregular, cuenta 60 segundos).",
            "Anota si el ritmo es regular o irregular y si el pulso es fuerte o débil.",
            "Compara con el valor del monitor; si difieren mucho, revisa los electrodos/sensor.",
        ],
    },
    "temperatura": {
        "titulo": "Cómo medir la temperatura corporal",
        "palabras": ["temperatura", "termometro"],
        "pasos": [
            "Usa el termómetro del botiquín de la misión (timpánico, frontal u oral) según su instructivo.",
            "Si es oral, evita comer o beber en los minutos previos; si es timpánico, tira suavemente de la oreja.",
            "Espera la señal del equipo antes de retirarlo y anota el valor.",
            "Si la lectura es anómala, repite en 5 minutos con la misma técnica.",
        ],
    },
    "respiracion": {
        "titulo": "Cómo medir la frecuencia respiratoria",
        "palabras": ["respiracion", "respiratoria", "respiraciones", "respira"],
        "pasos": [
            "Sin avisar a la persona (para no alterar su ritmo), observa el movimiento de pecho y abdomen.",
            "Cuenta las respiraciones durante 30 segundos y multiplica por 2.",
            "Observa el esfuerzo (uso de músculos del cuello), el color de labios y si puede hablar con frases completas.",
            "Anota el valor, la hora y cualquier signo de dificultad.",
        ],
    },
}

# --------------------------------------------------------------------------- emergencias
EMERGENCIAS = {
    "hipoxia": {
        "titulo": "Hipoxia: saturación de oxígeno baja / dificultad respiratoria",
        "palabras": ["hipoxia", "oxigeno", "saturacion", "falta de aire", "ahogo", "cianosis",
                     "no puedo respirar", "disnea", "dificultad para respirar"],
        "pasos": [
            "Avisa a la tripulación de inmediato y pide que alguien acompañe al afectado.",
            "Verifica el sensor: recoloca el pulsioxímetro, calienta la mano y repite la medición.",
            "Revisa el ambiente: ventilación del módulo, nivel de O₂ y de CO₂. Una atmósfera mala afecta a todos.",
            "Si la lectura se confirma (< 90 %), administra oxígeno suplementario con mascarilla según el protocolo de la misión.",
            "Mantén a la persona en reposo, aflojando ropa ajustada y animándola a respirar lento y profundo.",
            "Vuelve a medir cada 1-2 minutos y registra la tendencia.",
        ],
        "escalar": "Contacta al cirujano de vuelo / Control de Misión. Si la SpO₂ sigue < 90 %, hay confusión, labios azulados o pérdida de conciencia: emergencia mayor (evaluar evacuación al módulo seguro).",
    },
    "taquicardia": {
        "titulo": "Taquicardia: frecuencia cardíaca alta",
        "palabras": ["taquicardia", "palpitaciones", "corazon", "latidos rapidos",
                     "frecuencia cardiaca alta", "pulso alto", "pulso rapido"],
        "pasos": [
            "Pide a la persona que se detenga y descanse; sujétala en una posición cómoda.",
            "Confirma el valor tomando el pulso manualmente (arteria radial).",
            "Pregunta por síntomas: dolor o presión en el pecho, mareo, falta de aire, desmayo.",
            "Busca causas comunes: ejercicio reciente, deshidratación, fiebre, dolor, estrés, cafeína.",
            "Hidrata si está consciente y puede tragar; pide respiración lenta (inhalar 4 s, exhalar 6 s).",
            "Reevalúa cada 2-3 minutos.",
        ],
        "escalar": "Si supera 130-150 lpm en reposo por varios minutos, o hay dolor torácico, desmayo o falta de aire: avisa al cirujano de vuelo. Si pierde la conciencia y no respira normal: inicia RCP y prepara el desfibrilador.",
    },
    "bradicardia": {
        "titulo": "Bradicardia: frecuencia cardíaca baja",
        "palabras": ["bradicardia", "pulso bajo", "latidos lentos", "pulso lento"],
        "pasos": [
            "Confirma con pulso manual y revisa que los electrodos/sensores estén bien colocados.",
            "Pregunta por síntomas: mareo, debilidad, confusión, desmayo, dolor de pecho.",
            "Si hay síntomas, mantén a la persona asegurada y en reposo; no la dejes sola.",
            "Revisa medicamentos recientes en su ficha médica que puedan bajar el pulso.",
            "Monitorea cada 2 minutos.",
        ],
        "escalar": "Si hay síntomas o el pulso baja de 40 lpm, avisa de inmediato al cirujano de vuelo. Sin respuesta y sin respiración normal: RCP.",
    },
    "hipertension": {
        "titulo": "Hipertensión: presión arterial alta",
        "palabras": ["hipertension", "presion alta", "tension alta", "dolor de cabeza fuerte"],
        "pasos": [
            "Reposo de 5 minutos y repite la medición con el brazalete bien colocado (a la altura del corazón).",
            "Pregunta por síntomas: dolor de cabeza intenso, visión borrosa, dolor de pecho, falta de aire, confusión.",
            "Revisa la ficha: ¿tiene hipertensión conocida o medicación habitual? ¿La tomó hoy?",
            "Evita esfuerzo, cafeína y sal; hidrata con moderación.",
            "No administres fármacos antihipertensivos sin indicación del cirujano de vuelo.",
            "Mide cada 5-10 minutos y registra los valores.",
        ],
        "escalar": "Si la sistólica supera 180 mmHg o hay síntomas neurológicos o de pecho, es una urgencia: avisa a la tripulación y al cirujano de vuelo.",
    },
    "hipotension": {
        "titulo": "Hipotensión / posible shock: presión arterial baja",
        "palabras": ["hipotension", "presion baja", "desmayo", "mareo", "shock", "palidez"],
        "pasos": [
            "Asegura a la persona con correas y mantenla en reposo; en microgravedad no sirve 'acostarla con las piernas arriba', prioriza que esté estable y observada.",
            "Repite la medición y toma el pulso: ¿rápido y débil? ¿piel fría, pálida y sudorosa?",
            "Busca la causa: deshidratación, sangrado, reacción a un medicamento, infección, dolor intenso.",
            "Si está consciente y puede tragar, ofrece líquidos en pequeños sorbos.",
            "Controla cualquier sangrado visible con presión directa.",
            "Monitorea presión, pulso y SpO₂ cada 2 minutos.",
        ],
        "escalar": "Presión sistólica < 90 mmHg con síntomas, o < 85 mmHg en cualquier caso: emergencia. Avisa a la tripulación y al cirujano de vuelo; prepara el equipo de soporte vital.",
    },
    "fiebre": {
        "titulo": "Fiebre: temperatura corporal alta",
        "palabras": ["fiebre", "temperatura alta", "calentura", "febril", "escalofrios"],
        "pasos": [
            "Confirma con una segunda medición de temperatura.",
            "Hidrata con frecuencia y reduce el abrigo y la actividad física.",
            "Revisa la ficha médica (alergias y medicamentos) antes de usar cualquier antipirético del botiquín, y sigue la dosis del protocolo/etiqueta.",
            "Pregunta por otros síntomas: tos, dolor de garganta, dolor abdominal, rigidez de cuello, erupciones.",
            "Si se sospecha una infección, limita el contacto cercano y usa mascarilla.",
            "Mide la temperatura cada 30-60 minutos y registra la evolución.",
        ],
        "escalar": "Temperatura ≥ 39 °C, fiebre que persiste más de 24 h, o confusión, rigidez de cuello o erupción: avisa al cirujano de vuelo.",
    },
    "hipotermia": {
        "titulo": "Hipotermia: temperatura corporal baja",
        "palabras": ["hipotermia", "temperatura baja", "mucho frio", "frio"],
        "pasos": [
            "Confirma con una segunda medición de temperatura.",
            "Revisa el control térmico del traje/módulo y abriga a la persona con mantas aislantes.",
            "Ofrece bebidas tibias (no calientes) si está consciente.",
            "Evita el calentamiento brusco; vigila pulso y respiración.",
            "Mide la temperatura cada 15 minutos.",
        ],
        "escalar": "Temperatura < 35 °C, confusión, temblor intenso o somnolencia: avisa al cirujano de vuelo.",
    },
}

# (parámetro, dirección de la alerta) -> protocolo a sugerir
MAPA_ALERTAS = {
    ("spo2", "baja"): "hipoxia", ("fr", "alta"): "hipoxia", ("fr", "baja"): "hipoxia",
    ("fc", "alta"): "taquicardia", ("fc", "baja"): "bradicardia",
    ("pas", "alta"): "hipertension", ("pad", "alta"): "hipertension",
    ("pas", "baja"): "hipotension", ("pad", "baja"): "hipotension",
    ("temp", "alta"): "fiebre", ("temp", "baja"): "hipotermia",
}

# --------------------------------------------------------------------------- medicamentos
MEDICAMENTOS = {
    "titulo": "Uso seguro de medicamentos del botiquín",
    "palabras": ["medicamento", "medicina", "botiquin", "pastilla", "dosis", "farmaco",
                 "analgesico", "antibiotico", "paracetamol", "ibuprofeno", "tomar algo"],
    "pasos": [
        "Revisa la ficha del astronauta: ALERGIAS, medicamentos actuales y condiciones antes de administrar nada.",
        "Usa solo fármacos del botiquín de la misión, siguiendo la etiqueta y el protocolo. La dosis exacta la confirma el oficial médico o el cirujano de vuelo.",
        "Si hay duda sobre alergia o interacción, NO lo administres y consulta.",
        "Manipula pastillas y líquidos sujetos (bolsas/contenedores) para que no floten ni se pierdan.",
        "Registra en la bitácora clínica: fármaco, dosis, hora y quién lo administró.",
        "Vigila 15-30 minutos: erupción, hinchazón de cara o labios, dificultad para respirar o mareo intenso indican reacción adversa.",
        "Reevalúa los signos vitales después de administrarlo.",
    ],
    "escalar": "Reacción alérgica grave (hinchazón, dificultad para respirar, caída de presión): alerta a toda la tripulación, usa el autoinyector de epinefrina del botiquín según el protocolo y contacta al cirujano de vuelo.",
}


# --------------------------------------------------------------------------- utilidades
def lista_numerada(pasos: list[str]) -> str:
    return "\n".join(f"{i}. {p}" for i, p in enumerate(pasos, 1))


def emergencia_md(clave: str) -> str:
    e = EMERGENCIAS[clave]
    return f"### {e['titulo']}\n{lista_numerada(e['pasos'])}\n\n**Cuándo escalar:** {e['escalar']}"


def medicion_md(clave: str) -> str:
    m = MEDICIONES[clave]
    return f"### {m['titulo']}\n{lista_numerada(m['pasos'])}"


def medicamentos_md() -> str:
    m = MEDICAMENTOS
    return f"### {m['titulo']}\n{lista_numerada(m['pasos'])}\n\n**Reacción grave:** {m['escalar']}"


def detectar(texto: str, catalogo: dict) -> list[str]:
    """Claves del catálogo cuyas palabras clave aparecen en el texto."""
    t = normalizar(texto)
    return [k for k, v in catalogo.items() if any(p in t for p in v["palabras"])]


def protocolos_para_alertas(alertas: list[dict]) -> list[str]:
    """Protocolos recomendados para una lista de alertas, sin repetir."""
    claves: list[str] = []
    for a in alertas:
        clave = MAPA_ALERTAS.get((a["parametro"], a["direccion"]))
        if clave and clave not in claves:
            claves.append(clave)
    return claves

# --------------------------------------------------------------------------- utilidades
def lista_numerada(pasos: list[str]) -> str:
    return "\n".join(f"{i}. {p}" for i, p in enumerate(pasos, 1))


def emergencia_md(clave: str) -> str:
    e = EMERGENCIAS[clave]
    return f"### {e['titulo']}\n{lista_numerada(e['pasos'])}\n\n**Cuándo escalar:** {e['escalar']}"


def medicion_md(clave: str) -> str:
    m = MEDICIONES[clave]
    return f"### {m['titulo']}\n{lista_numerada(m['pasos'])}"


def medicamentos_md() -> str:
    m = MEDICAMENTOS
    return f"### {m['titulo']}\n{lista_numerada(m['pasos'])}\n\n**Reacción grave:** {m['escalar']}"


def detectar(texto: str, catalogo: dict) -> list[str]:
    """Claves del catálogo cuyas palabras clave aparecen en el texto."""
    t = normalizar(texto)
    return [k for k, v in catalogo.items() if any(p in t for p in v["palabras"])]


def protocolos_para_alertas(alertas: list[dict]) -> list[str]:
    """Protocolos recomendados para una lista de alertas, sin repetir."""
    claves: list[str] = []
    for a in alertas:
        clave = MAPA_ALERTAS.get((a["parametro"], a["direccion"]))
        if clave and clave not in claves:
            claves.append(clave)
    return claves


def texto_referencia() -> str:
    """Todos los protocolos en texto plano, para el prompt de la IA."""
    partes = ["## Cómo realizar mediciones"]
    for m in MEDICIONES.values():
        partes.append(f"### {m['titulo']}\n{lista_numerada(m['pasos'])}")
    partes.append("## Emergencias")
    for e in EMERGENCIAS.values():
        partes.append(f"### {e['titulo']}\n{lista_numerada(e['pasos'])}\nEscalar: {e['escalar']}")
    partes.append("## Medicamentos")
    partes.append(f"{lista_numerada(MEDICAMENTOS['pasos'])}\nEscalar: {MEDICAMENTOS['escalar']}")
    return "\n\n".join(partes)# --------------------------------------------------------------------------- utilidades
