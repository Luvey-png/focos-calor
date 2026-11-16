from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from graficos import meses
from idioma import t

RUTA_SERIE = Path("data/gfas_arg_SERIE_MENSUAL_2003_2026.parquet")
RUTA_MAPA = Path("data/gfas_arg_MAPA_ANUAL_2003_2026.parquet")
COLS_SERIE = ["anio", "mes", "version_gfas", "celdas_activas",
              "co2_ton", "co_ton", "ch4_ton", "c_ton"]
COLS_MAPA = ["anio", "lat", "lon", "dias_activos",
             "co2_ton", "co_ton", "ch4_ton", "c_ton"]
GASES = {"co2": "co2_ton", "co": "co_ton", "ch4": "ch4_ton", "c": "c_ton"}


def _fmt(x, dec=2):
    """Número con 2 decimales: 3,727.78 en inglés y 3.727,78 en español."""
    s = f"{x:,.{dec}f}"
    if st.session_state.get("idioma", "en") == "es":
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


@st.cache_data(show_spinner=False)
def cargar_serie(version):
    d = pd.read_parquet(RUTA_SERIE)
    for c in ("co2_ton", "co_ton", "ch4_ton", "c_ton"):
        d[c] = d[c].astype("float64")
    return d


@st.cache_data(show_spinner=False, max_entries=6)
def cargar_mapa(version, anio):
    """Lee del parquet solo las filas del año pedido (poca memoria)."""
    m = pd.read_parquet(RUTA_MAPA, filters=[("anio", "==", anio)])
    for c in ("lat", "lon"):
        m[c] = m[c].astype("float32")
    return m


def grafico_serie(sr, col, nombre):
    d = sr.sort_values("fecha").assign(mt=lambda x: x[col] / 1e6)
    fig = px.line(
        d, x="fecha", y="mt", title=t("gas_t_serie", gas=nombre),
        labels={"fecha": "", "mt": t("gas_ejey", gas=nombre)},
    )
    v = d["version_gfas"].astype(str).reset_index(drop=True)
    for i in range(1, len(d)):
        if v.iloc[i] != v.iloc[i - 1]:  # marca los cambios de versión del producto
            x = d["fecha"].iloc[i].strftime("%Y-%m-%d")
            fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper",
                          line=dict(dash="dot", width=1))
            fig.add_annotation(x=x, y=1, yref="paper", text=v.iloc[i],
                               showarrow=False, yanchor="bottom", font=dict(size=10))
    fig.update_layout(height=380)
    return fig


def grafico_anual(sr, col, nombre):
    d = sr.groupby("anio", as_index=False)[col].sum().assign(mt=lambda x: x[col] / 1e6)
    fig = px.bar(d, x="anio", y="mt", title=t("gas_t_anual", gas=nombre),
                 labels={"anio": t("g_anio"), "mt": t("gas_ejey", gas=nombre)})
    fig.update_xaxes(dtick=1)
    return fig


def grafico_estacional(sr, col, nombre):
    ms = meses()
    d = sr.groupby("mes", as_index=False)[col].sum()
    n_anios = max(sr["anio"].nunique(), 1)
    d["mt"] = d[col] / 1e6 / n_anios  # promedio por año
    d["mes_nombre"] = d["mes"].map(lambda m: ms[int(m) - 1])
    return px.bar(d, x="mes_nombre", y="mt", category_orders={"mes_nombre": ms},
                  title=t("gas_t_estac", gas=nombre),
                  labels={"mes_nombre": t("g_mes"), "mt": t("gas_ejey", gas=nombre)})


def mapa_calor(m, col, nombre):
    d = m.assign(valor=m[col] / 1e3)  # kilotoneladas por celda y año
    tope = max(float(d["valor"].quantile(0.99)), 1e-9)  # evita que un extremo tape todo
    etiqueta = t("gas_unidad_celda", gas=nombre)
    centro = {"lat": -38.5, "lon": -64.0}
    try:
        fig = px.density_map(
            d, lat="lat", lon="lon", z="valor", radius=9, zoom=3.3, center=centro,
            color_continuous_scale="YlOrRd", range_color=(0, tope), opacity=0.85,
            height=550, labels={"valor": etiqueta})
    except Exception:  # por si la versión de Plotly no trae density_map
        fig = px.scatter_map(
            d, lat="lat", lon="lon", color="valor", zoom=3.3, center=centro,
            color_continuous_scale="YlOrRd", range_color=(0, tope), height=550,
            hover_data={"dias_activos": True, "valor": ":.2f"},
            labels={"valor": etiqueta})
    fig.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    return fig


def vista_gases():
    st.subheader(t("gas_titulo"))
    st.caption(t("gas_intro"))
    if not (RUTA_SERIE.exists() and RUTA_MAPA.exists()):
        st.warning(t("gas_faltan"))
        return
    s = cargar_serie(RUTA_SERIE.stat().st_mtime)
    faltan = [c for c in COLS_SERIE if c not in s.columns]
    if faltan:
        st.error(t("gas_cols", cols=", ".join(faltan)))
        return

    anios = [int(a) for a in sorted(s["anio"].unique())]
    c1, c2 = st.columns([2, 1])
    a0, a1 = c1.select_slider(t("gas_rango"), options=anios, value=(anios[0], anios[-1]))
    gas = c2.radio(t("gas_gas"), list(GASES), format_func=lambda k: t("gas_" + k),
                   horizontal=True)
    col, nombre = GASES[gas], t("gas_" + gas)

    sr = s[(s["anio"] >= a0) & (s["anio"] <= a1)].copy()
    sr["fecha"] = pd.to_datetime(dict(year=sr["anio"], month=sr["mes"], day=1))

    st.markdown("**" + t("gas_kpi_tit", a=a0, b=a1) + "**")
    for caja, k in zip(st.columns(4), GASES):
        caja.metric(t("gas_" + k) + " (Mt)", _fmt(sr[GASES[k]].sum() / 1e6))

    st.plotly_chart(grafico_serie(sr, col, nombre), use_container_width=True)
    st.caption(t("gas_vers", v=", ".join(sorted(sr["version_gfas"].astype(str).unique()))))
    parcial = [int(a) for a, n in sr.groupby("anio")["mes"].nunique().items() if n < 12]
    if parcial:
        st.caption(t("gas_parcial", anios=", ".join(map(str, parcial))))
    ca, cb = st.columns(2)
    ca.plotly_chart(grafico_anual(sr, col, nombre), use_container_width=True)
    cb.plotly_chart(grafico_estacional(sr, col, nombre), use_container_width=True)

    st.subheader(t("gas_mapa_sub"))
    anio_m = st.selectbox(t("gas_mapa_anio"), sorted(anios, reverse=True))
    m = cargar_mapa(RUTA_MAPA.stat().st_mtime, int(anio_m))
    if m.empty:
        st.info(t("gas_mapa_vacio"))
    else:
        st.plotly_chart(mapa_calor(m, col, nombre), use_container_width=True)
        st.caption(t("gas_mapa_cap"))
    st.info(t("gas_nota"))
    st.caption(t("gas_fuente"))