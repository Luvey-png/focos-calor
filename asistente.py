"""Asistente de IA de Igneus.

El asistente NO responde de memoria: antes de cada pregunta se arma un resumen
con los datos reales de la app (serie armonizada, períodos críticos, anomalías,
actividad reciente por provincia y por localidad) y se le pide al modelo que
responda solo con eso.

Proveedores soportados (se elige con .streamlit/secrets.toml):
    IA_PROVEEDOR = "anthropic" | "gemini" | "openai"
    IA_API_KEY   = "..."            # la clave del proveedor elegido
    IA_MODELO    = "..."            # opcional, para cambiar el modelo
También se aceptan ANTHROPIC_API_KEY, GEMINI_API_KEY u OPENAI_API_KEY.
Sin clave, la pestaña funciona en "modo sin IA" con un resumen automático.
"""
import os

import numpy as np
import pandas as pd
import requests

import armonizacion as arm
from extras import LUGARES, detecciones_cercanas

MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

MODELOS = {
    "anthropic": "claude-sonnet-5-5",
    "gemini": "gemini-3.6-flash",
    "openai": "gpt-4.1-mini",
}
RADIO_LUGAR_KM = 20
DIAS_RECIENTES = 30

INSTRUCCIONES = """Sos el asistente de Igneus, un observatorio de detecciones térmicas \
satelitales de Argentina hecho para el NASA Space Apps Challenge 2026 (desafío \
"Harmonization of MODIS and VIIRS Hot Spots", propuesto por la CONAE).

Reglas:
1. Respondé SOLO con los datos del bloque DATOS. Si algo no está ahí, decí que no \
tenés ese dato y sugerí qué pestaña de la app mirar ("Cerca de mí", "Armonización", \
"Mapa"). Nunca inventes cifras, fechas ni lugares.
2. Hablá de "detecciones térmicas" o "focos de calor", nunca de "incendios \
confirmados": un foco puede ser una quema agrícola u otra fuente de calor.
3. No predecís incendios. Podés decir qué meses son históricamente críticos y si \
la actividad reciente está por encima o por debajo de lo normal.
4. Las cifras históricas están en la escala armonizada "equivalente VIIRS S-NPP". \
Las cifras "recientes" son detecciones de todos los satélites sin duplicados.
5. Escribí en español rioplatense, claro y breve (máximo ~180 palabras salvo que \
pidan un informe), pensando en vecinos, brigadistas o productores. Usá cifras \
redondeadas.
6. Si la pregunta es sobre una emergencia en curso, recordá llamar al 100 \
(bomberos) o al 911 y seguir las indicaciones de Defensa Civil.
"""

PREGUNTAS_EJEMPLO = [
    "¿Cuáles son los meses más críticos en San Luis?",
    "¿Cómo viene este año comparado con lo normal?",
    "¿Hubo actividad en los últimos 30 días cerca de Merlo?",
    "¿Qué provincias tuvieron más detecciones recientes?",
]

PEDIDO_INFORME = """Escribí un INFORME SEMANAL para brigadas y Defensa Civil sobre \
el área seleccionada, con estos títulos: "Situación reciente", "Comparación con lo \
normal", "Períodos críticos que se vienen", "Zonas para observar" y \
"Limitaciones". Máximo 350 palabras. Usá solo los DATOS."""


# ---------- Configuración ----------
def _secreto(secrets, clave):
    try:
        if clave in secrets:
            return str(secrets[clave])
    except Exception:
        pass
    return os.environ.get(clave)


def configuracion(secrets):
    """Devuelve (proveedor, clave, modelo) o (None, None, None) si no hay clave."""
    prov = (_secreto(secrets, "IA_PROVEEDOR") or "").lower().strip()
    clave = _secreto(secrets, "IA_API_KEY")
    propias = {"anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY",
               "openai": "OPENAI_API_KEY"}
    if not prov:
        for p, k in propias.items():
            if _secreto(secrets, k):
                prov = p
                break
    if prov not in MODELOS:
        return None, None, None
    clave = clave or _secreto(secrets, propias[prov])
    if not clave:
        return None, None, None
    return prov, clave, _secreto(secrets, "IA_MODELO") or MODELOS[prov]


# ---------- Datos para el asistente ----------
def _climatologia(h):
    g = arm.mensual_total(h).dropna(subset=["armonizado"])
    return g.groupby("mes")["armonizado"].mean().reindex(range(1, 13))


def _criticos(clima):
    if clima.isna().all():
        return []
    umbral = clima.quantile(0.75)
    return [MESES_LARGOS[m - 1] for m in clima.index if clima[m] >= umbral]


ANIOS_NORMAL = 10  # "lo normal" = promedio de los últimos 10 años


def _ultimo_mes_completo(fin):
    return fin.month if fin.is_month_end else fin.month - 1


def _anio_vs_normal(h, fin):
    """Detecciones armonizadas del año del último dato, hasta el último mes completo,
    contra el promedio de los 10 años anteriores en los mismos meses.
    Devuelve (actual, normal, último mes) o None."""
    ult = _ultimo_mes_completo(fin)
    if ult < 1:
        return None
    g = arm.mensual_total(h).dropna(subset=["armonizado"])
    meses = range(1, ult + 1)
    actual = g[(g["anio"] == fin.year) & g["mes"].isin(meses)]["armonizado"].sum()
    previos = g[g["anio"].between(fin.year - ANIOS_NORMAL, fin.year - 1) & g["mes"].isin(meses)]
    if previos.empty or actual == 0:
        return None
    normal = previos.groupby("anio")["armonizado"].sum().mean()
    return actual, normal, ult


def _recientes(df, fin):
    d = df[(df["fecha"] > fin - pd.Timedelta(days=DIAS_RECIENTES)) & ~df["es_duplicado"]]
    return d


def resumen_provincias(h_arm, df):
    fin = df["fecha"].max()
    rec = _recientes(df, fin).groupby(df["provincia"].astype(str)).size()
    filas = []
    for prov, h in h_arm.groupby("provincia"):
        clima = _climatologia(h)
        if clima.isna().all():
            continue
        avn = _anio_vs_normal(h, fin)
        filas.append({
            "provincia": prov,
            "meses_criticos": ", ".join(_criticos(clima)),
            "promedio_mensual_por_mes": "/".join(str(int(round(v))) for v in clima.fillna(0)),
            f"recientes_{DIAS_RECIENTES}d": int(rec.get(prov, 0)),
            "anio_actual_vs_normal_10a": (f"{avn[0] / avn[1]:.2f}x" if avn and avn[1] else "s/d"),
        })
    return pd.DataFrame(filas).sort_values(f"recientes_{DIAS_RECIENTES}d", ascending=False)


def resumen_lugares(df):
    fin = df["fecha"].max()
    base = df[~df["es_duplicado"]]
    filas = []
    for lugar, (lat, lon) in LUGARES.items():
        c = detecciones_cercanas(base, lat, lon, RADIO_LUGAR_KM)
        if c.empty:
            filas.append({"lugar": lugar, "historicas": 0, "mes_pico": "-",
                          f"recientes_{DIAS_RECIENTES}d": 0, "ultima": "-"})
            continue
        mes_pico = c["fecha"].dt.month.value_counts().idxmax()
        rec = c[c["fecha"] > fin - pd.Timedelta(days=DIAS_RECIENTES)]
        filas.append({
            "lugar": lugar, "historicas": len(c),
            "mes_pico": MESES_LARGOS[mes_pico - 1],
            f"recientes_{DIAS_RECIENTES}d": len(rec),
            "ultima": c["fecha"].max().strftime("%d/%m/%Y"),
        })
    return pd.DataFrame(filas)


def contexto(h_arm, df, provincias, desde, hasta, tabla_prov, tabla_lug, validacion):
    """Texto con todos los datos que puede usar el modelo."""
    fin = df["fecha"].max()
    h_f = arm.filtrar(h_arm, provincias, desde, hasta)
    a = arm.anual(h_f).dropna(subset=["armonizado"])
    clima = _climatologia(h_f)
    an = arm.anomalias(h_f, 1.5)
    top = an[an["anomalo"]].sort_values("z", ascending=False).head(8)
    ult12 = an.sort_values("fecha").tail(12)
    avn = _anio_vs_normal(h_f, fin)
    area = ("toda Argentina" if len(provincias) >= h_arm["provincia"].nunique()
            else ", ".join(provincias))

    partes = [
        "DATOS",
        f"Fecha del último dato: {fin:%d/%m/%Y}. Base: NASA FIRMS (MODIS y VIIRS), "
        f"desde {df['fecha'].min():%m/%Y}. Escala histórica: equivalente VIIRS S-NPP.",
        f"Validación de la armonización (2019-2025, años no usados para ajustar): error "
        f"mensual {validacion.iloc[0, 1] * 100:.1f} % con nuestro método vs "
        f"{validacion.iloc[2, 1] * 100:.0f} % sumando satélites sin armonizar.",
        "",
        f"== ÁREA SELECCIONADA: {area} ({desde:%Y}-{hasta:%Y}) ==",
        "Detecciones armonizadas por año: "
        + "; ".join(f"{int(r.anio)}: {int(round(r.armonizado))}" for r in a.itertuples()),
        "Promedio por mes del año: "
        + "; ".join(f"{MESES_LARGOS[m - 1]}: {int(round(v))}" for m, v in clima.dropna().items()),
        "Meses críticos (25 % más alto): " + ", ".join(_criticos(clima)),
    ]
    if avn:
        partes.append(f"Año {fin.year} de enero a {MESES_LARGOS[avn[2] - 1]} (meses completos): "
                      f"{int(avn[0])} vs promedio {int(avn[1])} de los {ANIOS_NORMAL} años "
                      f"anteriores en los mismos meses ({avn[0] / avn[1]:.2f} veces lo normal). "
                      f"Nota: {fin.year} viene de datos de casi tiempo real y algunos meses se "
                      "estimaron desde NOAA-20/NOAA-21 porque faltaba S-NPP.")
    partes.append("Últimos 12 meses (armonizado | normal del mes): " + "; ".join(
        f"{r.fecha:%m/%Y}: {int(round(r.armonizado))} | {int(round(r.mean))}"
        for r in ult12.itertuples()))
    partes.append("Meses más atípicos de la historia (desvíos sobre lo normal): " + "; ".join(
        f"{r.fecha:%m/%Y}: {int(round(r.armonizado))} ({r.z:.1f} desvíos, {r.metodo})"
        for r in top.itertuples()))
    partes += [
        "",
        f"== PROVINCIAS (recientes = últimos {DIAS_RECIENTES} días, todos los satélites "
        "sin duplicados; promedio mensual de enero a diciembre en escala armonizada) ==",
        tabla_prov.to_csv(index=False),
        f"== LOCALIDADES (radio de {RADIO_LUGAR_KM} km, detecciones sin duplicados de "
        "todos los satélites; 'historicas' no está armonizado) ==",
        tabla_lug.to_csv(index=False),
    ]
    return "\n".join(partes)


# ---------- Llamada al modelo ----------
def responder(pregunta, historial, datos, proveedor, clave, modelo, max_tokens=900):
    sistema = INSTRUCCIONES + "\n\n" + datos
    msgs = [m for m in historial[-8:] if m["role"] in ("user", "assistant")]
    msgs = msgs + [{"role": "user", "content": pregunta}]
    if proveedor == "anthropic":
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": clave, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": modelo, "max_tokens": max_tokens, "system": sistema,
                  "messages": msgs},
            timeout=90)
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"])
    if proveedor == "gemini":
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
            headers={"x-goog-api-key": clave, "content-type": "application/json"},
            json={"system_instruction": {"parts": [{"text": sistema}]},
                  "contents": [{"role": "model" if m["role"] == "assistant" else "user",
                                "parts": [{"text": m["content"]}]} for m in msgs],
                  "generationConfig": {"maxOutputTokens": max_tokens}},
            timeout=90)
        r.raise_for_status()
        partes = r.json()["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in partes)
    if proveedor == "openai":
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"authorization": f"Bearer {clave}", "content-type": "application/json"},
            json={"model": modelo, "max_tokens": max_tokens,
                  "messages": [{"role": "system", "content": sistema}] + msgs},
            timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    raise ValueError(f"Proveedor desconocido: {proveedor}")


# ---------- Modo sin IA ----------
def resumen_sin_ia(h_arm, df, provincias, desde, hasta, tabla_prov):
    """Resumen automático armado con reglas, para cuando no hay clave de IA."""
    fin = df["fecha"].max()
    h_f = arm.filtrar(h_arm, provincias, desde, hasta)
    clima = _climatologia(h_f)
    crit = _criticos(clima)
    avn = _anio_vs_normal(h_f, fin)
    rec = _recientes(df[df["provincia"].astype(str).isin(provincias)], fin)
    txt = [f"**Meses históricamente críticos:** {', '.join(crit) or 'sin datos'}."]
    if avn:
        ratio = avn[0] / avn[1]
        estado = ("por encima" if ratio > 1.15 else "por debajo" if ratio < 0.85 else "cerca")
        cant = f"{int(avn[0]):,}".replace(",", ".")
        veces = f"{ratio:.1f}".replace(".", ",")
        txt.append(f"**{fin.year}, de enero a {MESES_LARGOS[avn[2] - 1]}:** {cant} detecciones "
                   f"armonizadas, {veces} veces el promedio de los últimos {ANIOS_NORMAL} años en "
                   f"los mismos meses ({estado} de lo normal).")
    txt.append(f"**Últimos {DIAS_RECIENTES} días:** {len(rec):,} detecciones (sin duplicados)."
               .replace(",", "."))
    t = tabla_prov[tabla_prov["provincia"].isin(provincias)].head(3)
    col = f"recientes_{DIAS_RECIENTES}d"
    if len(t) and t[col].sum() > 0:
        txt.append("**Provincias con más actividad reciente:** " + ", ".join(
            f"{r.provincia} ({getattr(r, col)})" for r in t.itertuples()) + ".")
    return "\n\n".join(txt)
