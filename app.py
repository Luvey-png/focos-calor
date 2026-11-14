import streamlit as st
import pandas as pd
import plotly.express as px
from graficos import grafico_mensual

st.set_page_config(page_title="Focos de calor - San Luis", layout="wide")

st.title("Focos de calor - San Luis")

st.warning(
    "⚠️ Un foco de calor NO es un incendio confirmado. "
    "Es una detección térmica satelital que puede tener otras causas. "
    "(Texto provisorio: Luis lo redacta.)"
)


@st.cache_data
def cargar_datos():
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

# Un único DataFrame filtrado que alimenta TODO lo demás
df_f = df[
    df["sensor"].isin(sensores)
    & (df["fecha"].dt.date >= desde)
    & (df["fecha"].dt.date <= hasta)
]

st.sidebar.write(f"Detecciones mostradas: **{len(df_f)}** de {len(df)}")

# ---------- Contenido ----------
if df_f.empty:
    st.error("No hay detecciones con esos filtros.")
    st.stop()

tab_mapa, tab_graf, tab_datos = st.tabs(["Mapa", "Gráficos", "Datos"])

with tab_mapa:
    st.subheader("Mapa de detecciones térmicas")
    fig_mapa = px.scatter_map(
        df_f,
        lat="latitud",
        lon="longitud",
        color="sensor",
        hover_data=["fecha", "confianza", "fuente"],
        zoom=7,
        height=550,
    )
    fig_mapa.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_mapa, use_container_width=True)

with tab_graf:
    st.subheader("Comparación de sensores")
    st.plotly_chart(grafico_mensual(df_f), use_container_width=True)

with tab_datos:
    st.dataframe(df_f)