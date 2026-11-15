import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import pyarrow.parquet as pq
from graficos import (
    grafico_mensual, grafico_calendario, grafico_anio_mes,
    grafico_comparacion_sensores, grafico_estacionalidad,
    grafico_confianza, grafico_provincias, cargar_oni, grafico_enso_mensual, grafico_enso_fases
)
from extras import (
    LUGARES, detecciones_cercanas, mapa_cercano, grafico_estacional_zona,
    grafico_anual_zona, cargar_quemas, marcar_quemas, resumen_quemas,
    grafico_senales, grafico_frp_mensual, grafico_anomalias, tabla_anomalias,
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
    "satelite", "frp", "diurno", "provincia", "region", "es_duplicado", "senal",
]


@st.cache_resource
def cargar_datos(version):
    ruta = Path("data/focos_real.parquet")
    if ruta.exists():
        disponibles = pq.read_schema(ruta).names
        cols = [c for c in COLUMNAS if c in disponibles]
        df = pd.read_parquet(ruta, columns=cols)
    else:
        df = pd.read_csv("data/focos_prueba.csv", parse_dates=["fecha"])
    for c in ("region", "provincia", "senal"):
        if c not in df.columns:
            df[c] = "Sin dato"
    if "es_duplicado" not in df.columns:
        df["es_duplicado"] = False
        for c in ("latitud", "longitud", "frp"):
            if c in df.columns:
                    rec = Path("data/focos_recientes.parquet")
    if ruta.exists() and rec.exists():
        r = pd.read_parquet(rec)
        r = r[r["fecha"] > df["fecha"].max()]
        r = r[[c for c in df.columns if c in r.columns]]
        for c in df.columns:
            if str(df[c].dtype) == "category" and c in r.columns:
                cats = df[c].cat.categories.union(pd.Index(r[c].astype(str).unique()))
                df[c] = df[c].cat.set_categories(cats)
                r[c] = pd.Categorical(r[c].astype(str), categories=cats)
                df = pd.concat([df, r], ignore_index=True)
                df[c] = df[c].astype("float32")
    return df


_rutas = [Path("data/focos_real.parquet"), Path("data/focos_recientes.parquet")]
df = cargar_datos(tuple(p.stat().st_mtime if p.exists() else 0 for p in _rutas))

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

(tab_mapa, tab_cal, tab_graf, tab_enso, tab_cerca,
 tab_origen, tab_quemas, tab_datos) = st.tabs([
    "Mapa", "Calendario", "Gráficos", "El Niño / La Niña",
    "Cerca de mí", "Origen (inferido)", "Quemas declaradas", "Datos",
])

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
    st.subheader("Intensidad térmica acumulada")
    st.plotly_chart(grafico_frp_mensual(df_f), use_container_width=True)
    st.caption(
            "Suma de la potencia radiativa (FRP, en MW) de las detecciones de cada mes. "
             "Es un indicador de intensidad térmica; NO mide gases ni emisiones de carbono."
        )
    st.subheader("Meses atípicos")
    umbral = st.slider("Umbral (desvíos sobre el promedio del mes)", 1.0, 3.0, 1.5, 0.1)
    st.plotly_chart(grafico_anomalias(df_f, umbral), use_container_width=True)
    tabla = tabla_anomalias(df_f, umbral)
    top = tabla[tabla["anomalo"]].sort_values("z", ascending=False).head(10)
    if len(top):
        st.dataframe(
            top.assign(mes=top["fecha"].dt.strftime("%Y-%m"))[
                ["mes", "detecciones", "media", "z"]
            ].round(1).rename(columns={"media": "promedio del mes", "z": "desvíos"}),
            hide_index=True,
        )
    st.caption("Compara cada mes con el mismo mes de los demás años. Dejá un solo sensor para una lectura consistente.")
    

with tab_enso:
    st.subheader("El Niño / La Niña y actividad térmica")
    ruta_oni = Path("data/oni.txt")
    if not ruta_oni.exists():
        st.warning("Falta el archivo data/oni.txt (índice ONI de NOAA).")
    else:
        rezago = st.slider(
            "Retraso entre el clima y la actividad (meses)", 0, 6, 0,
            help="El efecto de El Niño / La Niña puede tardar meses en notarse.",
        )
        oni = cargar_oni(str(ruta_oni), rezago)
        st.plotly_chart(grafico_enso_mensual(df_f, oni), use_container_width=True)
        st.plotly_chart(grafico_enso_fases(df_f, oni), use_container_width=True)
        st.caption(
            "Tip: para una serie consistente desde 2000, dejá solo MODIS en el "
            "filtro de sensor; VIIRS empieza en 2012 y cambia el nivel de los conteos. "
            "Probá también una región distinta: el efecto no es igual en todo el país."
        )
        st.info(
            "Esto muestra asociación, no causa. El ONI mide la temperatura del Pacífico "
            "ecuatorial. La actividad térmica también depende de quemas agrícolas, uso "
            "del suelo, sequías locales y otros factores. No se aplicó ningún test "
            "estadístico. Cada conteo es de detecciones térmicas, no de incendios confirmados."
        )

with tab_cerca:
    st.subheader("Detecciones cerca de un punto")
    st.caption("Usa los filtros de la barra lateral. Es información de detecciones satelitales, no un pronóstico ni una alerta oficial.")
    c1, c2, c3 = st.columns(3)
    lugar = c1.selectbox("Lugar", list(LUGARES) + ["Otro (coordenadas)"])
    if lugar == "Otro (coordenadas)":
        lat0 = c2.number_input("Latitud", value=-33.30, format="%.4f")
        lon0 = c3.number_input("Longitud", value=-66.34, format="%.4f")
    else:
        lat0, lon0 = LUGARES[lugar]
    c4, c5 = st.columns(2)
    radio = c4.slider("Radio (km)", 1, 100, 20)
    dias = c5.slider("Ventana reciente (días)", 7, 365, 30)

    quemas = cargar_quemas()
    cercanas = marcar_quemas(detecciones_cercanas(df_f, lat0, lon0, radio), quemas)
    fin = df_f["fecha"].max()
    recientes = cercanas[cercanas["fecha"] >= fin - pd.Timedelta(days=int(dias))]
    st.info(
        f"Los datos cargados llegan hasta el {fin:%d/%m/%Y}. 'Reciente' se mide "
        "hasta esa fecha; los últimos días reales requieren el módulo de actualización."
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Detecciones recientes", int(len(recientes)))
    m2.metric("Dentro de una quema declarada", int(recientes["quema_autorizada"].sum()))
    m3.metric("Históricas en la zona", int(len(cercanas)))
    st.plotly_chart(mapa_cercano(recientes, lat0, lon0, radio, quemas), use_container_width=True)
    if len(recientes):
        st.warning(
            f"Hay {len(recientes)} detecciones térmicas dentro de {radio} km en la ventana "
            "elegida. Es una señal para observar: no confirma incendios."
        )
    else:
        st.success("Sin detecciones en ese radio y ventana.")
    if len(cercanas):
        ca, cb = st.columns(2)
        ca.plotly_chart(grafico_estacional_zona(cercanas), use_container_width=True)
        cb.plotly_chart(grafico_anual_zona(cercanas), use_container_width=True)

with tab_origen:
    st.subheader("Señales sobre el posible origen (inferidas)")
    st.warning(
        "Son señales calculadas con reglas simples. NO indican la causa real "
        "(accidental, natural o controlada) ni confirman incendios."
    )
    if (df_f["senal"].astype(str) == "Sin dato").all():
        st.info("Falta correr agregar_senales.py y subir el parquet actualizado.")
    else:
        st.plotly_chart(grafico_senales(df_f), use_container_width=True)
        tot = df_f["senal"].value_counts().rename_axis("señal").reset_index(name="detecciones")
        st.dataframe(tot, hide_index=True)
        muestra = df_f.sample(min(len(df_f), 20000), random_state=1)
        muestra = muestra.assign(senal=muestra["senal"].astype(str))
        fig_o = px.scatter_map(muestra, lat="latitud", lon="longitud", color="senal",
                               hover_data=["fecha", "provincia"], zoom=3.5,
                               center={"lat": -38.5, "lon": -64.0}, height=500)
        fig_o.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_o, use_container_width=True)
        st.caption(
            "Reglas (en orden de prioridad): 1) Recurrente: detecciones en el mismo punto "
            "(~1 km) en 10 o más años distintos. 2) Alta intensidad: FRP en el 5% más alto "
            "de su sensor. 3) Temporada de quemas: el resto de las detecciones de julio a "
            "octubre. 4) Sin señal particular. Las reglas son provisorias."
        )

with tab_quemas:
    st.subheader("Quemas controladas declaradas")
    quemas = cargar_quemas()
    if quemas.empty:
        st.info("No hay quemas cargadas en data/quemas_autorizadas.csv.")
    else:
        if "es_ejemplo" in quemas.columns and quemas["es_ejemplo"].any():
            st.warning("La tabla incluye datos de EJEMPLO inventados.")
        st.dataframe(resumen_quemas(df, quemas), hide_index=True)
    st.caption(
        "Cada fila es una quema declarada por una autoridad (con su fuente). "
        "'detecciones_en_zona' cuenta detecciones satelitales en ese radio y fechas."
    )
    
with tab_datos:
    st.dataframe(df_f.head(5000))
    st.caption("Se muestran las primeras 5.000 filas.")