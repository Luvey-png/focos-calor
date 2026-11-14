from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
from graficos import (
    grafico_mensual, grafico_calendario, grafico_anio_mes,
    grafico_comparacion_sensores, grafico_estacionalidad, grafico_confianza,
)

st.set_page_config(page_title="Focos de calor - Argentina", layout="wide")

st.title("Focos de calor - Argentina")
st.warning(
    "⚠️ Un foco de calor NO es un incendio confirmado. "
    "Es una detección térmica satelital que puede tener otras causas. "
    "(Texto provisorio: Luis lo redacta.)"
)


@st.cache_data
def cargar_datos():
    ruta = Path("data/focos_real.parquet")
    if ruta.exists():
        return pd.read_parquet(ruta)
    return pd.read_csv("data/focos_prueba.csv", parse_dates=["fecha"])


df = cargar_datos()

if df["es_prueba"].any():
    st.info("Estás viendo datos de PRUEBA, no datos reales.")

# ---------- Barra lateral: filtros ----------
st.sidebar.header("Filtros")

sensores = st.sidebar.multiselect(
    "Sensor",
    options=sorted(df["sensor"].unique()),
    default=sorted(df["sensor"].unique()),
)

fmin = df["fecha"].min().date()
fmax = df["fecha"].max().date()
rango = st.sidebar.date_input(
    "Rango de fechas", value=(fmin, fmax), min_value=fmin, max_value=fmax
)

# date_input devuelve 1 fecha mientras el usuario elige la segunda
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    desde, hasta = rango
else:
    desde, hasta = fmin, fmax

REGIONES = {
    "Toda Argentina": None,
    "Noroeste (aprox.)": (-29.5, -21.7, -69.0, -62.0),
    "Noreste (aprox.)": (-29.5, -21.7, -62.0, -53.6),
    "Centro / Cuyo (aprox.)": (-35.5, -29.5, -70.5, -61.0),
    "Pampa (aprox.)": (-40.0, -33.0, -64.0, -57.0),
    "Patagonia (aprox.)": (-55.1, -40.0, -73.6, -62.0),
    "San Luis (aprox.)": (-36.0, -31.8, -67.5, -64.7),
}
region = st.sidebar.selectbox("Región", list(REGIONES.keys()))

# Un único DataFrame filtrado que alimenta TODO lo demás
mask = (
    df["sensor"].isin(sensores)
    & (df["fecha"].dt.date >= desde)
    & (df["fecha"].dt.date <= hasta)
)
caja = REGIONES[region]
if caja is not None:
    lat_min, lat_max, lon_min, lon_max = caja
    mask &= df["latitud"].between(lat_min, lat_max) & df["longitud"].between(lon_min, lon_max)
df_f = df[mask]

st.sidebar.write(f"Detecciones mostradas: **{len(df_f)}** de {len(df)}")

# ---------- Contenido ----------
if df_f.empty:
    st.error("No hay detecciones con esos filtros.")
    st.stop()

tab_mapa, tab_cal, tab_graf, tab_datos = st.tabs(
    ["Mapa", "Calendario", "Gráficos", "Datos"]
)

with tab_mapa:
    st.subheader("Mapa de detecciones térmicas")
    MAX_PUNTOS = 20000
    df_mapa = df_f
    if len(df_f) > MAX_PUNTOS:
        df_mapa = df_f.sample(MAX_PUNTOS, random_state=1)
        st.caption(
            f"Se muestran {MAX_PUNTOS:,} puntos al azar de {len(df_f):,}. "
            "Acotá fechas o sensor para ver más detalle."
        )
    fig_mapa = px.scatter_map(
        df_mapa,
        lat="latitud",
        lon="longitud",
        color="sensor",
        hover_data=["fecha", "confianza", "fuente"],
        zoom=3.5,
        center={"lat": -38.5, "lon": -64.0},
        height=550,
    )
    fig_mapa.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_mapa, use_container_width=True)

with tab_cal:
    st.subheader("Calendario de actividad térmica")
    anios = sorted(df_f["fecha"].dt.year.unique(), reverse=True)
    anio = st.selectbox("Año", anios)
    st.plotly_chart(grafico_calendario(df_f, anio), use_container_width=True)
    st.plotly_chart(grafico_anio_mes(df_f), use_container_width=True)
    st.caption(
        "Cada valor es un conteo de detecciones térmicas, no de incendios confirmados."
    )

with tab_graf:
    st.subheader("Comparación de sensores")
    st.plotly_chart(grafico_comparacion_sensores(df_f), use_container_width=True)
    st.plotly_chart(grafico_mensual(df_f), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_estacionalidad(df_f), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_confianza(df_f), use_container_width=True)
    st.info(
        "Los sensores no son directamente comparables en cantidad: VIIRS tiene "
        "mayor resolución y detecta focos más pequeños que MODIS. Además, VIIRS "
        "cubre desde 2012 y MODIS desde 2000. Cada conteo es de detecciones "
        "térmicas, no de incendios confirmados."
    )

with tab_datos:
    st.dataframe(df_f)