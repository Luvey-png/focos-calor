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
import armonizacion as arm
import asistente as ia
from idioma import (
    t, selector_idioma, region_txt, num, formato_fecha, fecha_txt, senal_txt, motivo_txt, valid_txt,
)

st.set_page_config(
    page_title=f"{NOMBRE} · Focos de calor",
    page_icon=str(ICONO) if ICONO.exists() else "🔥",
    layout="wide",
)

aplicar_estilo()

st.markdown("""
<style>
[role="tablist"] {
    gap: 8px !important;
    padding: 8px 8px 16px 8px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,107,53,0.35) !important;
    border-radius: 14px !important;
}
[data-baseweb="tab-border"] { display: none !important; }
[data-baseweb="tab-highlight"] {
    display: block !important;
    background: #ffd60a !important;
    height: 4px !important;
    bottom: 4px !important;
    border-radius: 4px !important;
}
[role="tab"], [data-baseweb="tab"] {
    background: rgba(255,107,53,0.12) !important;
    border: 1px solid rgba(255,107,53,0.40) !important;
    border-radius: 10px !important;
    padding: 8px 14px !important;
    height: auto !important;
}
[role="tab"]:hover, [data-baseweb="tab"]:hover {
    background: rgba(255,60,30,0.30) !important;
}
[role="tab"][aria-selected="true"], [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(180deg, #ff3d00 0%, #c1121f 100%) !important;
    border: 2px solid #ffd60a !important;
    box-shadow: 0 0 14px rgba(255,61,0,0.75) !important;
}
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

selector_idioma()

COLUMNAS = [
    "sensor", "fecha", "latitud", "longitud", "confianza", "es_prueba",
    "satelite", "frp", "diurno", "provincia", "region", "es_duplicado", "senal",
]

OTRO = "Otro (coordenadas)"
MOTIVOS = [
    "Manejo de pastizal o pastura", "Limpieza de rastrojo agrícola",
    "Cortafuego / prevención", "Manejo de residuos vegetales",
    "Quema prescripta (manejo del fuego)", "Otro",
]


def _lugar_txt(x):
    return t("otro_coord") if x == OTRO else x


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
        if len(r):
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
_version = tuple(p.stat().st_mtime if p.exists() else 0 for p in _rutas)
df = cargar_datos(_version)
@st.cache_data(show_spinner=False)
def tramo_sin_datos(version):
    fechas = df["fecha"].drop_duplicates().sort_values()
    return int(fechas.diff().dt.days.max())

@st.cache_resource
def preparar_armonizacion(_df, version):
    m = arm.tabla_mensual(_df)
    return m, arm.armonizar(m), arm.validar(m)


@st.cache_resource
def preparar_asistente(_df, _h_arm, version):
    return ia.resumen_provincias(_h_arm, _df), ia.resumen_lugares(_df)
@st.cache_data(show_spinner=False, max_entries=10)
def contexto_ia(_h, _df, provincias, desde, hasta, _tprov, _tlug, _val, version):
    return ia.contexto(_h, _df, list(provincias), desde, hasta, _tprov, _tlug, _val)


encabezado(df)

if df["es_prueba"].any():
    st.info(t("prueba"))

# ---------- Barra lateral: filtros ----------
st.sidebar.header(t("filtros"))

armonizado = st.sidebar.checkbox(
    t("quitar_dup"), value=True, help=t("quitar_dup_help"),
)

lista_sensores = sorted(map(str, df["sensor"].unique()))
sensores = st.sidebar.multiselect(t("sensor"), lista_sensores, default=lista_sensores)

fmin = df["fecha"].min().date()
fmax = df["fecha"].max().date()
rango = st.sidebar.date_input(
    t("rango"), value=(fmin, fmax), min_value=fmin, max_value=fmax,
    format=formato_fecha(),
)
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    desde, hasta = rango
else:
    desde, hasta = fmin, fmax

regiones = [t("toda_arg")] + sorted(map(str, df["region"].unique()))
region = st.sidebar.selectbox(t("region"), regiones, format_func=region_txt)
if region == t("toda_arg"):
    provs_disp = sorted(map(str, df["provincia"].unique()))
else:
    provs_disp = sorted(map(str, df.loc[df["region"] == region, "provincia"].unique()))
provincias = st.sidebar.multiselect(
    t("provincia"), provs_disp, default=provs_disp, key=f"prov_{region}"
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
_hueco = tramo_sin_datos(_version)
if _hueco > 10:
    st.warning(t("tramo", dias=_hueco))

st.sidebar.write(t("det_mostradas", n=num(len(df_f)), total=num(len(df))))

# ---------- Contenido ----------
if df_f.empty:
    st.error(t("sin_det"))
    st.stop()

(tab_mapa, tab_cerca, tab_arm, tab_ia, tab_graf, tab_cal, tab_enso, tab_gases,
 tab_origen, tab_quemas, tab_metodo, tab_datos) = st.tabs([
    t("tab_mapa"), t("tab_cerca"), t("tab_arm"), t("tab_ia"), t("tab_graf"),
    t("tab_cal"), t("tab_enso"), t("tab_gases"), t("tab_origen"), t("tab_quemas"),
    t("tab_metodo"), t("tab_datos"),
])

with tab_ia:
    st.subheader(t("ia_titulo"))
    st.caption(t("ia_caption"))
    _m, _h, (_val, _, _) = preparar_armonizacion(df, _version)
    _tprov, _tlug = preparar_asistente(df, _h, _version)
    datos_ia = contexto_ia(_h, df, tuple(provincias), desde, hasta, _tprov, _tlug, _val, _version)
    proveedor, clave_ia, modelo_ia = ia.configuracion(st.secrets)

    if "chat" not in st.session_state:
        st.session_state.chat = []

    if proveedor is None:
        st.warning(t("ia_sin_ia"))
        st.markdown(ia.resumen_sin_ia(_h, df, provincias, desde, hasta, _tprov))
    else:
        cols = st.columns(len(ia.PREGUNTAS_EJEMPLO) + 1)
        pedido = None
        for i, q in enumerate(ia.PREGUNTAS_EJEMPLO):
            if cols[i].button(q, key=f"ej_{i}", use_container_width=True):
                pedido = q
        if cols[-1].button(t("ia_informe"), use_container_width=True):
            pedido = ia.PEDIDO_INFORME

        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["visible"] if "visible" in msg else msg["content"])

        escrita = st.chat_input(t("ia_placeholder"))
        pregunta = escrita or pedido
        if pregunta:
            visible = (t("ia_informe") if pregunta == ia.PEDIDO_INFORME else pregunta)
            with st.chat_message("user"):
                st.markdown(visible)
            with st.chat_message("assistant"):
                with st.spinner(t("ia_spinner")):
                    try:
                        resp = ia.responder(pregunta, st.session_state.chat, datos_ia,
                                            proveedor, clave_ia, modelo_ia)
                    except Exception as e:
                        resp = None
                        detalle = ""
                        r_e = getattr(e, "response", None)
                        if r_e is not None:
                            detalle = t("ia_cod", c=r_e.status_code, d=r_e.text[:300])
                        st.error(t("ia_error", tipo=type(e).__name__, detalle=detalle))
                if resp:
                    st.markdown(resp)
            if resp:
                st.session_state.chat += [
                    {"role": "user", "content": pregunta, "visible": visible},
                    {"role": "assistant", "content": resp},
                ]
        if st.session_state.chat and st.button(t("ia_borrar")):
            st.session_state.chat = []
            st.rerun()
        st.caption(t("ia_modelo", prov=proveedor, modelo=modelo_ia))

    with st.expander(t("ia_datos")):
        st.text(datos_ia)

with tab_mapa:
    st.subheader(t("mapa_titulo"))
    c1, c2 = st.columns(2)
    modo = c1.radio(t("mapa_modo"), ["recientes", "aleatoria"],
                    format_func=lambda k: t("modo_" + k), horizontal=True)
    max_pts = c2.slider(t("mapa_max"), 1000, 50000, 20000, 1000)
    df_mapa = df_f
    if len(df_f) > max_pts:
        if modo == "recientes":
            df_mapa = df_f.nlargest(max_pts, "fecha")
        else:
            df_mapa = df_f.sample(max_pts, random_state=1)
        st.caption(t("mapa_nota", n=num(max_pts), total=num(len(df_f)),
                     modo=t("modo_" + modo).lower()))
    fig_mapa = px.scatter_map(
        df_mapa,
        lat="latitud",
        lon="longitud",
        color="sensor",
        hover_data=["fecha", "provincia", "confianza"],
        labels={"sensor": t("sensor"), "fecha": t("col_fecha"),
                "provincia": t("provincia"), "confianza": t("col_confianza")},
        zoom=3.5,
        center={"lat": -38.5, "lon": -64.0},
        height=550,
    )
    fig_mapa.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_mapa, use_container_width=True)

with tab_cal:
    st.subheader(t("cal_titulo"))
    anios = sorted(df_f["fecha"].dt.year.unique(), reverse=True)
    anio = st.selectbox(t("cal_anio"), anios)
    st.plotly_chart(grafico_calendario(df_f, int(anio)), use_container_width=True)
    st.plotly_chart(grafico_anio_mes(df_f), use_container_width=True)
    st.caption(t("cal_nota"))

with tab_arm:
    st.subheader(t("arm_sub"))
    st.markdown(t("arm_intro"))
    m_arm, h_arm, (val_tabla, val_serie, val_corte) = preparar_armonizacion(df, _version)
    h_f = arm.filtrar(h_arm, provincias, desde, hasta)
    st.caption(t("arm_cap"))
    if h_f["armonizado"].notna().sum() == 0:
        st.info(t("arm_sin"))
    else:
        a_f = arm.anual(h_f)
        _ult = df["fecha"].max()
        _parcial = _ult.year if (_ult.month, _ult.day) != (12, 31) else None
        st.plotly_chart(arm.grafico_antes_despues(a_f, _parcial), use_container_width=True)
        st.plotly_chart(arm.grafico_calendario_armonizado(h_f), use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(arm.grafico_periodos_criticos(h_f), use_container_width=True)
        with c2:
            umbral_a = st.slider(t("arm_umbral"), 1.0, 3.0, 1.5, 0.1, key="umbral_arm")
            an = arm.anomalias(h_f, umbral_a)
            top_a = an[an["anomalo"]].sort_values("z", ascending=False).head(8)
            st.dataframe(
                top_a.assign(mes=top_a["fecha"].dt.strftime("%m/%Y"),
                             armonizado=top_a["armonizado"].round(),
                             normal=top_a["mean"].round(), z=top_a["z"].round(1))[
                    ["mes", "armonizado", "normal", "z", "metodo"]].rename(
                    columns={"mes": t("col_mes"), "armonizado": t("col_det"),
                             "normal": t("col_normal"), "z": t("col_desvios"),
                             "metodo": t("col_fuente")}),
                hide_index=True,
            )
        st.plotly_chart(arm.grafico_anomalias_armonizadas(an, umbral_a), use_container_width=True)

    st.subheader(t("arm_valid_sub"))
    st.markdown(t("arm_valid_txt", corte=val_corte, corte1=val_corte + 1))
    val_tabla = val_tabla.assign(Método=val_tabla["Método"].map(valid_txt))
    val_tabla = val_tabla.rename(columns={"Método": t("h_col_metodo")})
    st.dataframe(
        val_tabla.assign(**{c: (val_tabla[c] * 100).round(1).astype(str) + " %"
                            for c in ("Error mensual país", "Error anual por provincia")}
                         ).rename(columns={"Error mensual país": t("arm_err_mes"),
                                           "Error anual por provincia": t("arm_err_anual")}),
        hide_index=True,
    )
    st.plotly_chart(arm.grafico_validacion(val_serie, val_corte), use_container_width=True)

    with st.expander(t("arm_fac_exp")):
        fac, fac_nac = arm.tabla_factores(m_arm, provincias)
        st.dataframe(fac)
        st.caption(t("arm_fac_cap", nac=f"{fac_nac:.1f}", min=arm.MIN_DET))
    st.info(t("arm_como"))

with tab_graf:
    ruta_sup = Path("data/superficies.csv")
    if ruta_sup.exists():
        st.plotly_chart(
            grafico_densidad_provincias(df_f, pd.read_csv(ruta_sup)),
            use_container_width=True,
        )
    st.subheader(t("graf_comp"))
    st.plotly_chart(grafico_provincias(df_f), use_container_width=True)
    st.plotly_chart(grafico_comparacion_sensores(df_f), use_container_width=True)
    st.plotly_chart(grafico_mensual(df_f), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grafico_estacionalidad(df_f), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_confianza(df_f), use_container_width=True)
    st.info(t("graf_info"))
    st.subheader(t("graf_frp_sub"))
    st.plotly_chart(grafico_frp_mensual(df_f), use_container_width=True)
    st.caption(t("graf_frp_cap"))
    st.subheader(t("graf_atip_sub"))
    umbral = st.slider(t("graf_umbral"), 1.0, 3.0, 1.5, 0.1)
    st.plotly_chart(grafico_anomalias(df_f, umbral), use_container_width=True)
    tabla = tabla_anomalias(df_f, umbral)
    top = tabla[tabla["anomalo"]].sort_values("z", ascending=False).head(10)
    if len(top):
        st.dataframe(
            top.assign(mes=top["fecha"].dt.strftime("%Y-%m"))[
                ["mes", "detecciones", "media", "z"]
            ].round(1).rename(columns={"mes": t("col_mes"), "detecciones": t("col_det"),
                                       "media": t("col_prom"), "z": t("col_desvios")}),
            hide_index=True,
        )
    st.caption(t("graf_atip_cap"))

with tab_enso:
    st.subheader(t("enso_sub"))
    ruta_oni = Path("data/oni.txt")
    if not ruta_oni.exists():
        st.warning(t("enso_falta"))
    else:
        rezago = st.slider(t("enso_rezago"), 0, 6, 0, help=t("enso_help"))
        oni = cargar_oni(str(ruta_oni), rezago)
        st.plotly_chart(grafico_enso_mensual(df_f, oni), use_container_width=True)
        st.plotly_chart(grafico_enso_fases(df_f, oni), use_container_width=True)
        st.caption(t("enso_tip"))
        st.info(t("enso_info"))

with tab_cerca:
    st.subheader(t("cerca_sub"))
    st.caption(t("cerca_cap"))
    with st.expander(t("cm_titulo")):
        st.markdown(t("cm_md"))
    c1, c2, c3 = st.columns(3)
    lugar = c1.selectbox(t("cerca_lugar"), list(LUGARES) + [OTRO], format_func=_lugar_txt)
    if lugar == OTRO:
        lat0 = c2.number_input(t("lat"), value=-33.30, format="%.4f")
        lon0 = c3.number_input(t("lon"), value=-66.34, format="%.4f")
    else:
        lat0, lon0 = LUGARES[lugar]
    c4, c5 = st.columns(2)
    radio = c4.slider(t("radio"), 1, 100, 20)
    dias = c5.slider(t("ventana"), 7, 365, 30)

    quemas = cargar_quemas()
    cercanas = marcar_quemas(detecciones_cercanas(df_f, lat0, lon0, radio), quemas)
    fin = df_f["fecha"].max()
    recientes = cercanas[cercanas["fecha"] >= fin - pd.Timedelta(days=int(dias))]
    st.info(t("cerca_info", fin=fecha_txt(fin)))
    m1, m2, m3 = st.columns(3)
    m1.metric(t("m_rec"), int(len(recientes)))
    m2.metric(t("m_quema"), int(recientes["quema_autorizada"].sum()))
    m3.metric(t("m_hist"), int(len(cercanas)))
    st.plotly_chart(mapa_cercano(recientes, lat0, lon0, radio, quemas), use_container_width=True)
    if len(recientes):
        st.warning(t("cerca_warn", n=len(recientes), radio=radio))
    else:
        st.success(t("cerca_ok"))
    if len(cercanas):
        ca, cb = st.columns(2)
        ca.plotly_chart(grafico_estacional_zona(cercanas), use_container_width=True)
        cb.plotly_chart(grafico_anual_zona(cercanas), use_container_width=True)

with tab_origen:
    st.subheader(t("or_sub"))
    st.warning(t("or_warn"))
    if (df_f["senal"] == "Sin dato").all():
        st.info(t("or_falta"))
    else:
        st.plotly_chart(grafico_senales(df_f), use_container_width=True)
        vc = df_f["senal"].value_counts()
        vc = vc[vc > 0]
        tot = pd.DataFrame({t("col_senal"): [senal_txt(x) for x in vc.index],
                            t("col_det"): vc.values})
        st.dataframe(tot, hide_index=True)
        muestra = df_f.sample(min(len(df_f), 20000), random_state=1)
        muestra = muestra.assign(senal=muestra["senal"].astype(str).map(senal_txt))
        fig_o = px.scatter_map(muestra, lat="latitud", lon="longitud", color="senal",
                               hover_data=["fecha", "provincia"], zoom=3.5,
                               labels={"senal": t("col_senal"), "fecha": t("col_fecha"),
                                       "provincia": t("provincia")},
                               center={"lat": -38.5, "lon": -64.0}, height=500)
        fig_o.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_o, use_container_width=True)
        st.caption(t("or_reglas"))

with tab_quemas:
    st.subheader(t("q_sub"))
    st.warning(t("q_warn"))
    provs_form = sorted(map(str, df["provincia"].unique()))
    with st.form("form_quema", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input(t("f_nombre"))
        rango = c2.text_input(t("f_rango"))
        organizacion = c1.text_input(t("f_org"))
        permiso = c2.text_input(t("f_permiso"))
        motivo = st.selectbox(t("f_motivo"), MOTIVOS, format_func=motivo_txt)
        detalle = st.text_input(t("f_detalle"))
        c3, c4 = st.columns(2)
        prov_q = c3.selectbox(t("f_prov"), provs_form)
        lugar_q = c4.text_input(t("f_lugar"))
        ref = st.selectbox(t("f_ubic"), [OTRO] + list(LUGARES), format_func=_lugar_txt)
        c5, c6 = st.columns(2)
        lat_q = c5.number_input(t("f_lat"), value=-33.30, format="%.4f")
        lon_q = c6.number_input(t("lon"), value=-66.34, format="%.4f")
        c7, c8, c9 = st.columns(3)
        hoy = pd.Timestamp.today().date()
        f_ini = c7.date_input(t("f_inicio"), value=hoy, format=formato_fecha())
        f_fin = c8.date_input(t("f_fin"), value=hoy, format=formato_fecha())
        radio_q = c9.slider(t("f_radio"), 0.5, 20.0, 2.0, 0.5)
        acepto = st.checkbox(t("f_acepto"))
        enviar = st.form_submit_button(t("f_enviar"))

    if enviar:
        obligatorios = {t("o_nombre"): nombre, t("o_rango"): rango,
                        t("o_org"): organizacion, t("o_lugar"): lugar_q}
        faltan = [k for k, v in obligatorios.items() if not v.strip()]
        if faltan:
            st.error(t("q_complete", campos=", ".join(faltan)))
        elif f_fin < f_ini:
            st.error(t("q_fin"))
        elif (f_fin - f_ini).days > 14:
            st.error(t("q_14"))
        elif not acepto:
            st.error(t("q_acepto"))
        else:
            lat, lon = (lat_q, lon_q) if ref == OTRO else LUGARES[ref]
            guardar_quema({
                "provincia": prov_q, "lugar": lugar_q.strip(), "organizacion": organizacion.strip(),
                "motivo": motivo + (f" - {detalle.strip()}" if detalle.strip() else ""),
                "fecha_inicio": f_ini, "fecha_fin": f_fin, "latitud": lat, "longitud": lon,
                "radio_km": radio_q, "fuente": f"Declaración de {organizacion.strip()}",
                "es_ejemplo": False, "estado": "Declarada (sin verificar)",
                "nombre": nombre.strip(), "rango": rango.strip(), "permiso": permiso.strip(),
                "registrado_en": pd.Timestamp.now().isoformat(timespec="seconds"),
            })
            st.success(t("q_ok"))

    quemas = cargar_quemas()
    if quemas.empty:
        st.info(t("q_vacio"))
    else:
        st.dataframe(resumen_quemas(df, quemas), hide_index=True)
    st.caption(t("q_cap"))

    with st.expander(t("q_admin")):
        clave = st.text_input(t("q_clave"), type="password")
        try:
            ok = bool(clave) and clave == st.secrets["ADMIN_KEY"]
        except Exception:
            ok = False
        if ok:
            p = Path("data/quemas_declaradas.csv")
            if p.exists():
                st.download_button(t("q_desc"), p.read_bytes(),
                                   "quemas_declaradas.csv", "text/csv")
            else:
                st.info(t("q_no_decl"))

with tab_metodo:
    st.subheader(t("m_sub"))
    sats = ", ".join(sorted(map(str, df["satelite"].unique()))) if "satelite" in df.columns else "-"
    st.markdown(t(
        "m_md",
        n=num(len(df)),
        f0=fecha_txt(df["fecha"].min()),
        f1=fecha_txt(df["fecha"].max()),
        sensores=", ".join(sorted(map(str, df["sensor"].unique()))),
        sats=sats,
    ))
    st.caption(t("m_cap"))

with tab_gases:
    st.info(t("gases_info"))

with tab_datos:
    st.dataframe(df_f.head(5000))
    st.caption(t("d_cap"))
    if st.button(t("d_btn")):
        csv = df_f.nlargest(200000, "fecha").to_csv(index=False).encode("utf-8")
        st.download_button(t("d_dl"), csv, "focos_seleccion.csv", "text/csv")