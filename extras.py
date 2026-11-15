import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from graficos import _conteo_mensual, MESES

# Coordenadas aproximadas de ciudades (se puede ampliar)
LUGARES = {
    "Buenos Aires": (-34.60, -58.38), "Córdoba": (-31.42, -64.18),
    "Rosario": (-32.95, -60.65), "Mendoza": (-32.89, -68.84),
    "San Luis": (-33.30, -66.34), "Salta": (-24.79, -65.41),
    "San Miguel de Tucumán": (-26.82, -65.22), "Resistencia": (-27.46, -58.98),
    "Formosa": (-26.18, -58.17), "Corrientes": (-27.47, -58.83),
    "Posadas": (-27.37, -55.90), "Santiago del Estero": (-27.79, -64.26),
    "San Salvador de Jujuy": (-24.19, -65.30), "Santa Fe": (-31.63, -60.70),
    "Paraná": (-31.73, -60.53), "Neuquén": (-38.95, -68.06),
    "Bahía Blanca": (-38.72, -62.27), "Mar del Plata": (-38.00, -57.55),
    "Santa Rosa": (-36.62, -64.29), "Catamarca": (-28.47, -65.78),
    "La Rioja": (-29.41, -66.86), "San Juan": (-31.54, -68.54),
    "Comodoro Rivadavia": (-45.86, -67.50), "Bariloche": (-41.13, -71.31),
    "Río Gallegos": (-51.62, -69.22), "Ushuaia": (-54.80, -68.30),
}

COLS_QUEMAS = ["provincia", "fecha_inicio", "fecha_fin", "latitud",
               "longitud", "radio_km", "fuente", "es_ejemplo"]


# ---------- Cerca de un punto ----------
def distancia_km(lat, lon, lat0, lon0):
    p1 = np.radians(lat0)
    p2 = np.radians(np.asarray(lat, dtype="float64"))
    dl = np.radians(np.asarray(lon, dtype="float64") - lon0)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def detecciones_cercanas(df, lat0, lon0, radio_km):
    dlat = radio_km / 111.0
    dlon = radio_km / (111.0 * max(np.cos(np.radians(lat0)), 0.2))
    caja = df[
        df["latitud"].between(lat0 - dlat, lat0 + dlat)
        & df["longitud"].between(lon0 - dlon, lon0 + dlon)
    ].copy()
    caja["dist_km"] = distancia_km(caja["latitud"].values, caja["longitud"].values, lat0, lon0)
    return caja[caja["dist_km"] <= radio_km].sort_values("fecha", ascending=False)


def mapa_cercano(recientes, lat0, lon0, radio_km, quemas=None):
    zoom = float(np.clip(11 - np.log2(max(radio_km, 1) / 2), 4, 11))
    centro = dict(lat=lat0, lon=lon0)
    if len(recientes):
        fig = px.scatter_map(
            recientes, lat="latitud", lon="longitud", color="sensor",
            hover_data=["fecha", "dist_km", "confianza"], height=500,
        )
    else:
        fig = go.Figure()
    ang = np.linspace(0, 2 * np.pi, 90)
    fig.add_trace(go.Scattermap(
        lat=lat0 + (radio_km / 111.0) * np.sin(ang),
        lon=lon0 + (radio_km / (111.0 * np.cos(np.radians(lat0)))) * np.cos(ang),
        mode="lines", line=dict(width=2, color="black"),
        name=f"Radio {radio_km} km", hoverinfo="skip"))
    fig.add_trace(go.Scattermap(
        lat=[lat0], lon=[lon0], mode="markers",
        marker=dict(size=14, color="black"), name="Tu punto", hoverinfo="name"))
    if quemas is not None and len(quemas):
        fig.add_trace(go.Scattermap(
            lat=quemas["latitud"], lon=quemas["longitud"], mode="markers",
            marker=dict(size=12, color="green"), name="Quema declarada",
            text=quemas["fuente"].astype(str)))
    fig.update_layout(
        map=dict(center=centro, zoom=zoom, style="open-street-map"),
        margin=dict(l=0, r=0, t=0, b=0), height=500)
    return fig


def grafico_estacional_zona(d):
    c = d.groupby(d["fecha"].dt.month).size().reindex(range(1, 13), fill_value=0)
    c = c.reset_index()
    c.columns = ["mes", "detecciones"]
    c["mes_nombre"] = c["mes"].map(lambda m: MESES[m - 1])
    return px.bar(c, x="mes_nombre", y="detecciones",
                  category_orders={"mes_nombre": MESES},
                  title="Meses con actividad en esta zona (todos los años)",
                  labels={"mes_nombre": "Mes", "detecciones": "Detecciones"})


def grafico_anual_zona(d):
    c = d.groupby(d["fecha"].dt.year).size().reset_index()
    c.columns = ["anio", "detecciones"]
    return px.bar(c, x="anio", y="detecciones", title="Detecciones por año en esta zona",
                  labels={"anio": "Año", "detecciones": "Detecciones"})


# ---------- Quemas declaradas ----------
RUTA_DECLARADAS = "data/quemas_declaradas.csv"
COLS_DECL = ["provincia", "lugar", "organizacion", "motivo", "fecha_inicio", "fecha_fin",
             "latitud", "longitud", "radio_km", "fuente", "es_ejemplo", "estado",
             "nombre", "rango", "permiso", "registrado_en"]
COLS_PUBLICAS = ["provincia", "lugar", "organizacion", "motivo", "fecha_inicio",
                 "fecha_fin", "radio_km", "estado"]


def cargar_quemas(ruta="data/quemas_autorizadas.csv", ruta_decl=RUTA_DECLARADAS):
    partes = []
    for r in (ruta, ruta_decl):
        try:
            t = pd.read_csv(r, parse_dates=["fecha_inicio", "fecha_fin"])
        except (FileNotFoundError, pd.errors.EmptyDataError):
            continue
        if len(t):
            partes.append(t)
    q = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    q = q.reindex(columns=COLS_DECL)
    q["es_ejemplo"] = q["es_ejemplo"].astype(str).str.lower().eq("true")
    return q


def guardar_quema(datos, ruta=RUTA_DECLARADAS):
    from pathlib import Path
    p = Path(ruta)
    fila = pd.DataFrame([datos]).reindex(columns=COLS_DECL)
    fila.to_csv(p, mode="a", header=not p.exists(), index=False, encoding="utf-8")


def resumen_quemas(df, quemas):
    """Tabla pública: sin nombre, rango ni permiso."""
    filas = []
    for _, q in quemas.iterrows():
        sub = df[(df["fecha"] >= q["fecha_inicio"]) & (df["fecha"] <= q["fecha_fin"])]
        n = len(detecciones_cercanas(sub, q["latitud"], q["longitud"], q["radio_km"])) if len(sub) else 0
        fila = {c: q.get(c) for c in COLS_PUBLICAS}
        fila["detecciones_en_zona"] = n
        filas.append(fila)
    return pd.DataFrame(filas)

def marcar_quemas(cercanas, quemas):
    """True si la detección cae en el radio y las fechas de una quema declarada."""
    c = cercanas.copy()
    c["quema_autorizada"] = False
    for _, q in quemas.iterrows():
        en_fecha = (c["fecha"] >= q["fecha_inicio"]) & (c["fecha"] <= q["fecha_fin"])
        d = distancia_km(c["latitud"].values, c["longitud"].values, q["latitud"], q["longitud"])
        c.loc[en_fecha & (d <= q["radio_km"]), "quema_autorizada"] = True
    return c

# ---------- Señales de origen (inferidas) ----------
# ---------- Intensidad y meses atípicos ----------
def grafico_senales(df):
    d = pd.DataFrame({"anio": df["fecha"].dt.year, "senal": df["senal"].astype(str)})
    c = d.groupby(["anio", "senal"]).size().reset_index(name="n")
    fig = px.bar(
        c, x="anio", y="n", color="senal",
        title="Señales por año (% de detecciones)",
        labels={"anio": "Año", "n": "%", "senal": ""},
    )
    fig.update_layout(barmode="stack", barnorm="percent")
    return fig


def tabla_anomalias(df, umbral=1.5):
    c = _conteo_mensual(df).dropna().copy()
    c["mes"] = c["fecha"].dt.month
    g = c.groupby("mes")["detecciones"]
    c["media"] = g.transform("mean")
    c["z"] = (c["detecciones"] - c["media"]) / g.transform("std")
    c["anomalo"] = c["z"] >= umbral
    return c


def grafico_anomalias(df, umbral=1.5):
    c = tabla_anomalias(df, umbral)
    c["tipo"] = c["anomalo"].map({True: "Muy por encima del promedio",
                                  False: "Dentro de lo habitual"})
    fig = px.bar(
        c, x="fecha", y="detecciones", color="tipo",
        color_discrete_map={"Muy por encima del promedio": "#d62728",
                            "Dentro de lo habitual": "#bdbdbd"},
        title="Meses con actividad térmica muy por encima de lo habitual",
        labels={"detecciones": "Detecciones", "fecha": "", "tipo": ""})
    fig.add_trace(go.Scatter(x=c["fecha"], y=c["media"], mode="lines",
                             name="Promedio histórico del mes",
                             line=dict(color="black", dash="dot", width=1)))
    fig.update_layout(height=420, legend_title_text="")
    return fig

def grafico_frp_mensual(df):
    d = df.assign(mes=df["fecha"].dt.to_period("M").dt.to_timestamp())
    c = d.groupby(["mes", "sensor"], observed=True)["frp"].sum().reset_index()
    return px.bar(c, x="mes", y="frp", color="sensor", barmode="group",
                  title="Intensidad térmica acumulada por mes (suma de FRP)",
                  labels={"mes": "", "frp": "Suma de FRP (MW)"})

def grafico_densidad_provincias(df, sup):
    c = df.groupby("provincia", observed=True).size().reset_index(name="n")
    c["provincia"] = c["provincia"].astype(str)
    c = c.merge(sup, on="provincia", how="inner")
    c["por_1000km2"] = c["n"] / c["km2"] * 1000
    c = c.sort_values("por_1000km2")
    return px.bar(
        c, x="por_1000km2", y="provincia", orientation="h",
        hover_data={"n": ":,", "km2": ":,.0f"},
        title="Detecciones cada 1.000 km² (comparable entre provincias)",
        labels={"por_1000km2": "Detecciones por 1.000 km²", "provincia": ""},
        height=max(350, 24 * len(c)),
    )