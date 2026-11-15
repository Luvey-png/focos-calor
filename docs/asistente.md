# Asistente de IA

**Rama:** `armonizacion-sensores`\
**Archivos:** `asistente.py` (nuevo), `app.py`, `extras.py`, `.streamlit/secrets.toml.example` (nuevo)\
**Fecha:** 15/11/2026

## 1. Qué hace

Es una pestaña nueva, **"Asistente IA"** (la primera de la app), donde cualquiera
puede preguntar en lenguaje simple. Por ejemplo:

- "¿Cuáles son los meses más críticos en San Luis?"
- "¿Cómo viene este año comparado con lo normal?"
- "¿Hubo actividad en los últimos 30 días cerca de Merlo?"
- "¿Qué provincias tuvieron más detecciones recientes?"

Tiene botones con esas preguntas de ejemplo y uno de **"Informe semanal para
brigadas"**, que genera un informe con estas secciones: situación reciente,
comparación con lo normal, períodos críticos que se vienen, zonas para observar y
limitaciones.

Responde a los tres usuarios que nombra la consigna: vecinos y brigadas (alerta
temprana y respuesta), gestores del territorio y científicos.

## 2. Cómo evita inventar datos

El modelo **no responde de memoria**. En cada pregunta, la app arma un bloque de
**DATOS** con información calculada de la base y se lo pasa al modelo con
instrucciones estrictas:

1. Responder solo con los DATOS. Si algo no está, decirlo y sugerir qué pestaña
   mirar.
2. Hablar de "detecciones térmicas", no de "incendios confirmados".
3. No predecir incendios: solo meses críticos y comparación con lo normal.
4. Aclarar que la escala histórica es "equivalente VIIRS S-NPP".
5. Escribir en español rioplatense, claro y breve.
6. Ante una emergencia, recordar llamar al 100 o al 911.

Los DATOS incluyen:

| Bloque | Contenido |
|---|---|
| Encabezado | Fecha del último dato, fuente y error de validación de la armonización |
| Área seleccionada (filtros de la barra lateral) | Serie anual armonizada, promedio de cada mes, meses críticos, año actual contra el promedio de los 10 años anteriores, últimos 12 meses y meses más atípicos |
| Provincias (las 24) | Meses críticos, promedio de cada mes, detecciones de los últimos 30 días y año actual contra lo normal |
| Localidades (28 ciudades, radio de 20 km) | Detecciones históricas, mes pico, últimos 30 días y fecha de la última detección |

Los DATOS se pueden ver en el desplegable **"Ver los datos que usa el asistente"**.
Sirve para el jurado (transparencia) y para revisar las respuestas.

**Cambio en `extras.py`:** se agregaron **Villa Mercedes** y **Merlo (San Luis)**
a `LUGARES`, así que también aparecen en "Cerca de mí".

## 3. Configuración

> **Paso a paso** (conseguir la clave, crear el archivo, probar y publicar):
> ver [`guia-paso-a-paso.md`](guia-paso-a-paso.md).

El asistente funciona con **Anthropic (Claude), Google (Gemini) u OpenAI**. Se
configura en `.streamlit/secrets.toml`, que ya está en `.gitignore`:

```toml
IA_PROVEEDOR = "gemini"        # "anthropic", "gemini" u "openai"
IA_API_KEY   = "tu-clave"
# IA_MODELO  = "gemini-2.5-flash"   # opcional
```

Se puede partir de `.streamlit/secrets.toml.example`. También se aceptan
`ANTHROPIC_API_KEY`, `GEMINI_API_KEY` u `OPENAI_API_KEY`, como secretos o como
variables de entorno.

Modelos por defecto (se cambian con `IA_MODELO` si alguno no está disponible):

| Proveedor | Modelo |
|---|---|
| anthropic | `claude-sonnet-5-5` |
| gemini | `gemini-2.5-flash` |
| openai | `gpt-4.1-mini` |

En **Streamlit Cloud**, la clave se carga en *Settings → Secrets* de la app, con
el mismo formato. **Nunca hay que subir la clave al repo.**

**Sin clave**, la pestaña funciona en **modo sin IA**: muestra un resumen
automático del área (meses críticos, año actual contra lo normal, últimos 30 días
y provincias con más actividad), calculado con reglas. Sirve de respaldo si en la
demo falla internet o la clave.

## 4. Estructura de `asistente.py`

| Función | Qué hace |
|---|---|
| `configuracion(secrets)` | Lee proveedor, clave y modelo |
| `resumen_provincias(h_arm, df)` | Tabla por provincia para los DATOS |
| `resumen_lugares(df)` | Tabla por localidad para los DATOS |
| `contexto(...)` | Arma el bloque de DATOS completo (~6.000 caracteres) |
| `responder(pregunta, historial, datos, ...)` | Llama a la API del proveedor con `requests`. Manda las últimas 8 intervenciones de la conversación |
| `resumen_sin_ia(...)` | Resumen por reglas para el modo sin IA |

En `app.py`, `preparar_asistente(...)` calcula las tablas de provincias y
localidades una sola vez y las guarda en caché (unos 2 segundos). El bloque de DATOS
se rearma en cada consulta según los filtros.

No hace falta instalar nada nuevo: `requests` ya viene con Streamlit.

## 5. Cambio relacionado en la armonización

Al preparar el asistente apareció un problema en los datos recientes de 2026: de
enero a julio solo hay **NOAA-21**, y en noviembre S-NPP tiene 2 días de datos. Por
eso 2026 aparecía casi vacío. Se corrigió en `armonizacion.py`:

- Un satélite cuenta como disponible en un mes si tiene datos en al menos el 70 %
  de los días.
- Si falta S-NPP, se estima desde NOAA-20 y, si no, desde NOAA-21.

Los detalles y los nuevos números de validación están en `docs/armonizacion.md`.

## 6. Límites

- Las respuestas las genera un modelo de IA: pueden tener errores. La app lo
  aclara debajo del chat.
- Los datos de 2026 son de casi tiempo real, y algunos meses están estimados desde
  NOAA-20 o NOAA-21.
- "Lo normal" es el promedio de los 10 años anteriores en los mismos meses, hasta
  el último mes completo.
- Las localidades usan detecciones sin duplicados pero **no armonizadas**: sirven
  para comparar dentro de la misma localidad, no entre épocas de satélites
  distintas.
- El asistente no tiene información de clima, viento ni alertas oficiales.
- No se probó con claves reales en este entorno. Se probó la integración con
  respuestas simuladas de los tres proveedores. **Antes de la demo hay que probarlo
  con la clave real.**

## 7. Uso de IA (para la declaración de Space Apps)

- **IA dentro del producto:** el asistente usa un modelo de lenguaje del proveedor
  configurado para redactar respuestas a partir de datos calculados por la app.
- **IA usada para construirlo:** el código de este módulo se desarrolló con ayuda
  de un asistente de IA (Claude).
