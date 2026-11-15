import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import pyarrow.parquet as pq
from graficos import (
    grafico_mensual, grafico_calendario, grafico_anio_mes,
    grafico_comparacion_sensores, grafico_estacionalidad,
    grafico_confianza, grafico_provincias, cargar_oni, grafico_enso_mensual, grafico_enso_fases, 
)
from extras import (
    LUGARES, detecciones_cercanas, mapa_cercano, grafico_estacional_zona,
    grafico_anual_zona, cargar_quemas, marcar_quemas, resumen_quemas, guardar_quema,
    grafico_senales, grafico_frp_mensual, grafico_anomalias, tabla_anomalias, grafico_densidad_provincias
)
from estilo import NOMBRE, ICONO, aplicar_estilo, encabezado

st.set_page_config(
    page_title=f"{NOMBRE} · Focos de calor",
    page_icon=str(ICONO) if ICONO.exists() else "🔥",
    layout="wide",
)
aplicar_estilo()

COLUMNAS = [
    "sensor", "fecha", "latitud", "longitud", "confianza", "es_prueba",
    "satelite", "frp", "diurno", "provincia", "region", "es_duplicado", "senal",
]


@st.cache_resource
def cargar_datos(version):
    ruta = Path("data/focos_real.parquet")
    rec = Path("data/focos_recientes.parquet")

    if ruta.exists():
        disponibles = pq.read_schema(ruta).names
        cols = [c for c in COLUMNAS if c in disponibles]
        df = pd.read_parquet(ruta, columns=cols)
    else:
        df = pd.read_csv("data/focos_prueba.csv", parse_dates=["fecha"])

    # Sumar los datos recientes (solo los posteriores al último día del histórico)
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

    for c in ("region", "provincia", "senal"):
        if c not in df.columns:
            df[c] = "Sin dato"
    if "es_duplicado" not in df.columns:
        df["es_duplicado"] = False
    for c in ("latitud", "longitud", "frp"):
        if c in df.columns:
            df[c] = df[c].astype("float32")
    return df
_rutas = [Path("data/focos_real.parquet"), Path("data/focos_recientes.parquet")]
df = cargar_datos(tuple(p.stat().st_mtime if p.exists() else 0 for p in _rutas))
encabezado(df)

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
_dias = df["fecha"].drop_duplicates().sort_values().diff().dt.days
if _dias.max() > 10:
    st.warning(
        f"Hay un tramo de {int(_dias.max())} días sin datos en la base. "
        "Los conteos de ese período no son confiables."
    )

st.sidebar.write(f"Detecciones mostradas: **{len(df_f):,}** de {len(df):,}")

# ---------- Contenido ----------
if df_f.empty:
    st.error("No hay detecciones con esos filtros.")
    st.stop()

(tab_mapa, tab_cal, tab_graf, tab_enso, tab_gases, tab_cerca,
 tab_origen, tab_quemas, tab_metodo, tab_datos) = st.tabs([
    "Mapa", "Calendario", "Gráficos", "El Niño / La Niña", "Gases de carbono",
    "Cerca de mí", "Origen (inferido)", "Quemas", "Método y fuentes", "Datos",
])

with tab_mapa:
    st.subheader("Mapa de detecciones térmicas")
    c1, c2 = st.columns(2)
    modo = c1.radio("Qué puntos mostrar", ["Más recientes", "Muestra aleatoria"],
                    horizontal=True)
    max_pts = c2.slider("Cantidad máxima de puntos", 1000, 50000, 20000, 1000)
    df_mapa = df_f
    if len(df_f) > max_pts:
        if modo == "Más recientes":
            df_mapa = df_f.nlargest(max_pts, "fecha")
        else:
            df_mapa = df_f.sample(max_pts, random_state=1)
        st.caption(
            f"Se muestran {max_pts:,} de {len(df_f):,} detecciones ({modo.lower()}). "
            "Los gráficos y conteos usan TODAS las detecciones filtradas. "
            "Acotá fechas o provincia para ver todos los puntos en el mapa."
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
    ruta_sup = Path("data/superficies.csv")
    if ruta_sup.exists():
        st.plotly_chart(
            grafico_densidad_provincias(df_f, pd.read_csv(ruta_sup)),
            use_container_width=True,
        )
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
    st.subheader("Quemas controladas")
    st.warning(
        "Este registro reúne **declaraciones** de quemas controladas. NO es un permiso, "
        "no reemplaza la autorización de la autoridad competente y las declaraciones "
        "no están verificadas."
    )
    provs_form = sorted(map(str, df["provincia"].unique()))
    with st.form("form_quema", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre y apellido *")
        rango = c2.text_input("Rango / cargo *")
        organizacion = c1.text_input("Organización *")
        permiso = c2.text_input("N° de permiso o expediente (si tiene)")
        motivo = st.selectbox("Motivo *", [
            "Manejo de pastizal o pastura", "Limpieza de rastrojo agrícola",
            "Cortafuego / prevención", "Manejo de residuos vegetales",
            "Quema prescripta (manejo del fuego)", "Otro"])
        detalle = st.text_input("Detalle del motivo (opcional)")
        c3, c4 = st.columns(2)
        prov_q = c3.selectbox("Provincia *", provs_form)
        lugar_q = c4.text_input("Lugar (paraje, campo, referencia) *")
        ref = st.selectbox("Ubicación", ["Otro (coordenadas)"] + list(LUGARES))
        c5, c6 = st.columns(2)
        lat_q = c5.number_input("Latitud (si elegiste coordenadas)", value=-33.30, format="%.4f")
        lon_q = c6.number_input("Longitud", value=-66.34, format="%.4f")
        c7, c8, c9 = st.columns(3)
        hoy = pd.Timestamp.today().date()
        f_ini = c7.date_input("Inicio", value=hoy)
        f_fin = c8.date_input("Fin", value=hoy)
        radio_q = c9.slider("Radio aprox. (km)", 0.5, 20.0, 2.0, 0.5)
        acepto = st.checkbox("Declaro que la información es verdadera y que cuento con la autorización correspondiente.")
        enviar = st.form_submit_button("Registrar declaración")

    if enviar:
        obligatorios = {"nombre": nombre, "rango": rango, "organización": organizacion, "lugar": lugar_q}
        faltan = [k for k, v in obligatorios.items() if not v.strip()]
        if faltan:
            st.error("Completá: " + ", ".join(faltan))
        elif f_fin < f_ini:
            st.error("La fecha de fin no puede ser anterior al inicio.")
        elif (f_fin - f_ini).days > 14:
            st.error("Una declaración puede cubrir hasta 14 días.")
        elif not acepto:
            st.error("Tenés que aceptar la declaración.")
        else:
            lat, lon = (lat_q, lon_q) if ref == "Otro (coordenadas)" else LUGARES[ref]
            guardar_quema({
                "provincia": prov_q, "lugar": lugar_q.strip(), "organizacion": organizacion.strip(),
                "motivo": motivo + (f" - {detalle.strip()}" if detalle.strip() else ""),
                "fecha_inicio": f_ini, "fecha_fin": f_fin, "latitud": lat, "longitud": lon,
                "radio_km": radio_q, "fuente": f"Declaración de {organizacion.strip()}",
                "es_ejemplo": False, "estado": "Declarada (sin verificar)",
                "nombre": nombre.strip(), "rango": rango.strip(), "permiso": permiso.strip(),
                "registrado_en": pd.Timestamp.now().isoformat(timespec="seconds"),
            })
            st.success("Declaración registrada. Aparece abajo y en la pestaña 'Cerca de mí'.")

    quemas = cargar_quemas()
    if quemas.empty:
        st.info("Todavía no hay quemas declaradas.")
    else:
        st.dataframe(resumen_quemas(df, quemas), hide_index=True)
    st.caption(
        "El nombre, el rango y el permiso se guardan para trazabilidad y no se muestran. "
        "'detecciones_en_zona' cuenta detecciones satelitales en ese radio y fechas."
    )

    with st.expander("Administración (solo equipo)"):
        clave = st.text_input("Clave", type="password")
        try:
            ok = bool(clave) and clave == st.secrets["ADMIN_KEY"]
        except Exception:
            ok = False
        if ok:
            p = Path("data/quemas_declaradas.csv")
            if p.exists():
                st.download_button("Descargar registro completo", p.read_bytes(),
                                   "quemas_declaradas.csv", "text/csv")
            else:
                st.info("Todavía no hay declaraciones.")

with tab_metodo:
    st.subheader("Método, fuentes y límites")
    sats = ", ".join(sorted(map(str, df["satelite"].unique()))) if "satelite" in df.columns else "-"
    st.markdown(f"""
**Datos cargados:** {len(df):,} detecciones térmicas del {df['fecha'].min():%d/%m/%Y}
al {df['fecha'].max():%d/%m/%Y}. Satélites/sensores: {', '.join(sorted(map(str, df['sensor'].unique())))}
(satélites: {sats}).

**Fuentes**
- Detecciones térmicas: NASA FIRMS (MODIS y VIIRS), solo clase vegetación.
- Límites provinciales: API Georef del gobierno argentino.
- Fases El Niño / La Niña: Oceanic Niño Index de NOAA (CPC).

**Procesamiento**
1. Recorte a Argentina y asignación de provincia y región por ubicación.
2. Confianza unificada en baja / nominal / alta (MODIS 0-100 y VIIRS l/n/h).
3. Armonización entre sensores: una cuadrícula de 0,01° (~1 km) por día; se
   conserva la detección de mayor confianza y FRP. Puede unir también detecciones
   del mismo sensor y no une las que caen en celdas vecinas.
4. Los datos más recientes provienen de productos de casi tiempo real (NRT),
   que pueden cambiar cuando se publique la versión estándar.

**Límites que hay que tener presentes**
- Un foco de calor NO es un incendio confirmado: puede ser una quema agrícola,
  una fuente industrial u otra anomalía térmica.
- MODIS y VIIRS no son comparables en cantidad: VIIRS tiene mayor resolución.
- Las "señales de origen" son reglas simples, no la causa real.
- Los años o meses sin datos de algún sensor no significan ausencia de actividad.
- Las quemas declaradas dependen de que se carguen avisos oficiales con fuente.
""")
    st.caption("Texto científico a cargo de Luis; documentación de decisiones a cargo de A4.")

with tab_datos:
    st.dataframe(df_f.head(5000))
    st.caption("Se muestran las primeras 5.000 filas.")
    if st.button("Preparar descarga (hasta 200.000 filas más recientes)"):
        csv = df_f.nlargest(200000, "fecha").to_csv(index=False).encode("utf-8")
        st.download_button("Descargar CSV", csv, "focos_seleccion.csv", "text/csv")