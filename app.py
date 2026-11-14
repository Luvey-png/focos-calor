import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import pyarrow.parquet as pq
from graficos import (
    grafico_mensual, grafico_calendario, grafico_anio_mes,
    grafico_comparacion_sensores, grafico_estacionalidad,
    grafico_confianza, grafico_provincias,
)

st.set_page_config(page_title="Focos de calor - Argentina", layout="wide")
st.title("Focos de calor - Argentina")

st.warning(
    "⚠️ Un foco de calor NO es un incendio confirmado. "
    "Es una detección térmica satelital que puede tener otras causas. "
    "(Texto provisorio: Luis lo redacta.)"
)

COLUMNAS = [
    "sensor", "fecha", "latitud", "longitud", "confianza", "es_prueba",
    "satelite", "frp", "diurno", "provincia", "region", "es_duplicado",
]


@st.cache_resource  # no copia el DataFrame en cada clic; NO modificarlo afuera
def cargar_datos():
    ruta = Path("data/focos_real.parquet")
    if ruta.exists():
        disponibles = pq.read_schema(ruta).names
        cols = [c for c in COLUMNAS if c in disponibles]
        df = pd.read_parquet(ruta, columns=cols)
    else:
        df = pd.read_csv("data/focos_prueba.csv", parse_dates=["fecha"])
    for c in ("region", "provincia"):
        if c not in df.columns:
            df[c] = "Sin dato"
    if "es_duplicado" not in df.columns:
        df["es_duplicado"] = False
    return df


df = cargar_datos()

if df["es_prueba"].any():
    st.info("Estás viendo datos de PRUEBA, no datos reales.")

# ---------- Barra lateral: filtros ----------
st.sidebar.header("Filtros")

armonizado = st.sidebar.checkbox(
    "Armonizado (sin duplicados entre sensores)", value=True
)

lista_sensores = sorted(map(str, df["sensor"].unique()))
sensores = st.sidebar.multiselect("Sensor", lista_sensores, default=lista_sensores)

fmin = df["fecha"].min().date()
fmax = df["fecha"].max().date()
rango = st.sidebar.date_input(
    "Rango de fechas", value=(fmin, fmax), min_value=fmin, max_value=fmax
)
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    desde, hasta = rango
else:
    desde, hasta = fmin, fmax

regiones = ["Toda Argentina"] + sorted(map(str, df["region"].unique()))
region = st.sidebar.selectbox("Región", regiones)
if region == "Toda Argentina":
    provs_disp = sorted(map(str, df["provincia"].unique()))
else:
    provs_disp = sorted(map(str, df.loc[df["region"] == region, "provincia"].unique()))
provincias = st.sidebar.multiselect(
    "Provincia", provs_disp, default=provs_disp, key=f"prov_{region}"
)

# Un único DataFrame filtrado que alimenta TODO lo demás
mask = (
    df["sensor"].isin(sensores)
    & df["provincia"].isin(provincias)
    & (df["fecha"] >= pd.Timestamp(desde))
    & (df["fecha"] <= pd.Timestamp(hasta))
)
if armonizado:
    mask &= ~df["es_duplicado"]
df_f = df[mask]

st.sidebar.write(f"Detecciones mostradas: **{len(df_f):,}** de {len(df):,}")

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
            "Acotá fechas, sensor o provincia para ver más detalle."
        )
    fig_mapa = px.scatter_map(
        df_mapa,
        lat="latitud",
        lon="longitud",
        color="sensor",
        hover_data=["fecha", "provincia", "confianza"],
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
    st.plotly_chart(grafico_calendario(df_f, int(anio)), use_container_width=True)
    st.plotly_chart(grafico_anio_mes(df_f), use_container_width=True)
    st.caption(
        "Cada valor es un conteo de detecciones térmicas, no de incendios confirmados."
    )

with tab_graf:
    st.subheader("Comparación de sensores")
    st.plotly_chart(grafico_provincias(df_f), use_container_width=True)
    st.plotly_chart(grafico_comparacion_sensores(df_f), use_container_width=True)
    st.plotly_chart(grafico_mensual(df_f), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_estacionalidad(df_f), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_confianza(df_f), use_container_width=True)
    st.info(
        "Los sensores no son directamente comparables en cantidad: VIIRS tiene "
        "mayor resolución y detecta focos más pequeños que MODIS. VIIRS cubre "
        "desde 2012 y MODIS desde 2000. Faltan los datos anuales de MODIS de "
        "2005, 2010 y 2016 (un cero en esos años es ausencia de dato, no ausencia "
        "de actividad). Cada conteo es de detecciones térmicas, no de incendios "
        "confirmados."
    )

with tab_datos:
    st.dataframe(df_f.head(5000))
    st.caption("Se muestran las primeras 5.000 filas.")