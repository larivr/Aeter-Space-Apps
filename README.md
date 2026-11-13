# 🚀 AstroMonitor

Monitoreo de signos vitales de astronautas con alertas a la tripulación, historial médico y un asistente virtual con IA que guía en emergencias.

> **Prototipo educativo de hackatón.** Los datos son simulados y los protocolos son genéricos de ejemplo. No es un dispositivo médico ni sustituye al oficial médico ni al cirujano de vuelo.

## Qué incluye

| Requisito del reto | Dónde está |
|---|---|
| Monitoreo de presión, SpO₂, frecuencia cardíaca, temperatura y frecuencia respiratoria | Pestaña **Monitoreo en vivo** (métricas + gráficas con líneas de umbral) |
| Alertar a los demás ante una emergencia | Banner **"ALERTA A TODA LA TRIPULACIÓN"** en todas las pantallas, avisos emergentes, pestaña **Alertas** con reconocimiento |
| Base de datos de historial médico | Pestaña **Historial médico**: ficha, bitácora clínica, estadísticas, tendencias y exportación a CSV (SQLite) |
| Asistente virtual con IA (mediciones, medicamentos, emergencias) | Pestaña **Asistente IA** (Claude con contexto del paciente, o modo offline con protocolos locales) |

## Instalación

```bash
cd astromonitor
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar

```bash
# Opcional: activar la IA de Claude (sin esto el asistente funciona en modo offline)
export ANTHROPIC_API_KEY="tu-api-key"      # Windows PowerShell: $env:ANTHROPIC_API_KEY="tu-api-key"

streamlit run app.py
```

También puedes pegar la API key en la barra lateral de la app. Si usas otro modelo: `export ASTRO_MODELO="nombre-del-modelo"`.

## Guion de demo (3 minutos)

1. Muestra el panel en reposo: todo verde, gráficas estables.
2. En la barra lateral, elige **Hipoxia** y pulsa **Activar**.
3. En unos segundos la SpO₂ cae: aparece el aviso emergente y el banner rojo **"ALERTA A TODA LA TRIPULACIÓN"**.
4. Cambia "Sesión iniciada como" a otro tripulante (o abre otra pestaña del navegador): también ve la alerta. Pulsa **Reconocer**.
5. Ve a **Asistente IA** → **"Guíame en la emergencia actual"**: da pasos personalizados con los datos del paciente.
6. Pregunta por medicamentos: el asistente revisa las **alergias** de la ficha (prueba con Sofía Chaves, alérgica al ibuprofeno).
7. Pulsa **Normalizar**, muestra el **Historial médico** (estadísticas, bitácora, CSV).

## Arquitectura

```
 ┌───────────────┐  mediciones   ┌──────────┐   lee    ┌────────────────────┐
 │  simulador.py │ ───────────▶  │ SQLite   │ ◀─────── │ app.py (Streamlit) │
 │  (sensores)   │  + alertas    │ (db.py)  │          │  dashboard + chat  │
 └───────────────┘               └──────────┘          └─────────┬──────────┘
   servicio.py (hilo)  alertas.py (umbrales)                     │
                                                       asistente.py ──▶ Claude API
                                                        protocolos.py ─▶ modo offline
```

| Archivo | Función |
|---|---|
| `app.py` | Interfaz (dashboard, alertas, historial, chat) |
| `simulador.py` | Generador de datos de sensores |
| `servicio.py` | Hilo que mide cada segundo, guarda en la BD y dispara alertas |
| `alertas.py` | Umbrales y reglas (advertencia / crítica) |
| `db.py` | Base de datos SQLite (astronautas, mediciones, eventos, notas) |
| `asistente.py` | Asistente con IA + respaldo offline |
| `protocolos.py` | Protocolos de ejemplo: cómo medir, emergencias, medicamentos |

## El generador de datos

Cada signo vital "flota" hacia un valor objetivo con un poco de ruido:

```
valor_nuevo = valor + velocidad × (objetivo − valor) + ruido
```

- En **normal**, el objetivo es el valor base de cada astronauta (reposo).
- Un **escenario** cambia el objetivo de algunos signos (p. ej. hipoxia: SpO₂ → 80, FC → 120, FR → 27) y los valores bajan o suben de forma gradual, como en una emergencia real.
- **Normalizar** devuelve el objetivo al valor base y el paciente se recupera.

Pruébalo en la terminal: `python simulador.py`

Para agregar un escenario, añade una entrada en `ESCENARIOS` (en `simulador.py`) y su etiqueta en `ETIQUETAS_ESCENARIO`.

Para usar **sensores reales** (Arduino, pulsioxímetro Bluetooth, MQTT...), reemplaza `generar()` por una función que lea el dispositivo y devuelva el mismo diccionario: `{"fc", "pas", "pad", "spo2", "temp", "fr"}`. El resto del sistema no cambia.

## Umbrales de alerta (editables en `alertas.py`)

| Signo | Advertencia | Crítica |
|---|---|---|
| Frecuencia cardíaca | < 50 o > 110 lpm | < 40 o > 130 lpm |
| Presión sistólica | < 100 o > 140 mmHg | < 85 o > 180 mmHg |
| Presión diastólica | < 60 o > 90 mmHg | < 50 o > 110 mmHg |
| SpO₂ | < 94 % | < 90 % |
| Temperatura | < 36.0 o > 37.8 °C | < 35.0 o > 39.0 °C |
| Frecuencia respiratoria | < 10 o > 20 rpm | < 8 o > 28 rpm |

## Limitaciones y siguientes pasos

- Los umbrales y protocolos son de ejemplo: valídalos con fuentes oficiales (NASA Space Medicine, ISS Medical Checklist) antes de presentarlos como "reales".
- La base de datos guarda 1 medición por segundo por astronauta (~1 MB por hora con 4 astronautas); para una misión larga conviene reducir la frecuencia de guardado o agregar los datos.
- Mejoras posibles: modelo de IA local (p. ej. Ollama) para funcionar sin conexión con la Tierra, autenticación por tripulante, detección de anomalías con ML, más sensores (CO₂ ambiental, radiación, sueño) y notificaciones sonoras.
