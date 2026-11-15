import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from idioma import t

# Se mantienen en español porque otros módulos (extras.py) los importan.
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
DIAS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MESES_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _en():
    return st.session_state.get("idioma", "en") == "en"


def meses():
    return MESES_EN if _en() else MESES


def dias():
    return DIAS_EN if _en() else DIAS


def grafico_mensual(df):
    """Detecciones por mes y sensor. A3 puede reemplazar el contenido;
    el nombre y lo que recibe/devuelve NO cambian."""
    per = df["fecha"].dt.to_period("M")
    conteo = df.groupby([per, "sensor"], observed=True).size().reset_index(name="detecciones")
    conteo["mes"] = conteo["fecha"].dt.to_timestamp()
    conteo["sensor"] = conteo["sensor"].astype(str)
    conteo = conteo[["mes", "sensor", "detecciones"]]
    return px.line(
        conteo, x="mes", y="detecciones", color="sensor",
        title=t("g_t_mensual"),
        labels={"mes": t("g_mes"), "detecciones": t("g_det"), "sensor": t("g_sensor")},
    )


def grafico_calendario(df, anio):
    """Calendario diario de un año: un cuadrado por día."""
    f = df["fecha"]
    f = f[f.dt.year == anio]
    por_dia = f.value_counts()
    dias_anio = pd.date_range(f"{anio}-01-01", f"{anio}-12-31")
    por_dia = por_dia.reindex(dias_anio, fill_value=0)

    c = por_dia.rename("detecciones").rename_axis("fecha").reset_index()
    offset = dias_anio[0].weekday()
    c["semana"] = (c["fecha"].dt.dayofyear - 1 + offset) // 7
    c["dia_sem"] = c["fecha"].dt.weekday
    c["texto"] = c["fecha"].dt.strftime("%Y-%m-%d" if _en() else "%d/%m/%Y")

    z = c.pivot(index="dia_sem", columns="semana", values="detecciones")
    tx = c.pivot(index="dia_sem", columns="semana", values="texto")

    fig = go.Figure(go.Heatmap(
        z=z.values, x=z.columns, y=list(range(7)),
        customdata=tx.values,
        hovertemplate="%{customdata}<br>%{z:,d} " + t("g_det_lc") + "<extra></extra>",
        colorscale="YlOrRd", xgap=2, ygap=2,
        colorbar=dict(title=t("g_det")),
    ))
    # etiquetas de mes sobre el eje X (semana en que empieza cada mes)
    ms = meses()
    inicio_mes = c[c["fecha"].dt.day == 1]
    fig.update_xaxes(
        tickvals=inicio_mes["semana"].tolist(),
        ticktext=[ms[m - 1] for m in inicio_mes["fecha"].dt.month],
        showgrid=False,
    )
    fig.update_yaxes(
        tickvals=list(range(7)), ticktext=dias(),
        autorange="reversed", showgrid=False,
    )
    fig.update_layout(
        title=t("g_t_cal", anio=anio),
        height=300, margin=dict(l=40, r=20, t=60, b=30),
    )
    return fig


def grafico_anio_mes(df):
    """Mapa de calor: filas = años, columnas = meses."""
    f = df["fecha"]
    tab = f.groupby([f.dt.year.rename("anio"), f.dt.month.rename("mes")]).size().unstack(fill_value=0)
    tab = tab.reindex(columns=range(1, 13), fill_value=0)
    fig = px.imshow(
        tab.values, x=meses(), y=tab.index.astype(str),
        color_continuous_scale="YlOrRd", aspect="auto",
        labels=dict(x=t("g_mes"), y=t("g_anio"), color=t("g_det")),
        title=t("g_t_anio_mes"),
    )
    fig.update_layout(height=max(350, 22 * len(tab)))
    fig.update_traces(
        hovertemplate=t("g_anio") + " %{y} · %{x}<br>%{z:,d} "
        + t("g_det_lc") + "<extra></extra>"
    )
    return fig


def grafico_comparacion_sensores(df):
    """MODIS vs VIIRS: detecciones por año, una barra por sensor."""
    f = df["fecha"]
    conteo = (df.groupby([f.dt.year.rename("anio"), "sensor"], observed=True)
              .size().reset_index(name="detecciones"))
    conteo["sensor"] = conteo["sensor"].astype(str)
    fig = px.bar(
        conteo, x="anio", y="detecciones", color="sensor", barmode="group",
        title=t("g_t_comp"),
        labels={"anio": t("g_anio"), "detecciones": t("g_det"), "sensor": t("g_sensor")},
    )
    fig.update_xaxes(dtick=1)
    return fig


def grafico_estacionalidad(df):
    """Detecciones por mes del año (todos los años juntos), por sensor.
    Muestra en qué época del año hay más actividad."""
    ms = meses()
    f = df["fecha"]
    conteo = (df.groupby([f.dt.month.rename("mes"), "sensor"], observed=True)
              .size().reset_index(name="detecciones"))
    conteo["sensor"] = conteo["sensor"].astype(str)
    conteo["mes_nombre"] = conteo["mes"].map(lambda m: ms[m - 1])
    fig = px.line(
        conteo, x="mes_nombre", y="detecciones", color="sensor", markers=True,
        category_orders={"mes_nombre": ms},
        title=t("g_t_estac"),
        labels={"mes_nombre": t("g_mes"), "detecciones": t("g_det"),
                "sensor": t("g_sensor")},
    )
    return fig


def grafico_confianza(df):
    """Distribución de confianza por sensor (en porcentaje)."""
    conteo = df.groupby(["sensor", "confianza"], observed=True).size().reset_index(name="n")
    conteo["sensor"] = conteo["sensor"].astype(str)
    conteo["confianza"] = conteo["confianza"].astype(str)
    conteo["porcentaje"] = conteo["n"] / conteo.groupby("sensor")["n"].transform("sum") * 100
    niveles = ["baja", "nominal", "alta", "desconocida"]
    nombres = {n: t("g_conf_" + n) for n in niveles}
    conteo["confianza"] = conteo["confianza"].map(lambda x: nombres.get(x, x))
    fig = px.bar(
        conteo, x="sensor", y="porcentaje", color="confianza",
        category_orders={"confianza": list(nombres.values())},
        title=t("g_t_conf"),
        labels={"porcentaje": t("g_pct_det"), "confianza": t("g_confianza"),
                "sensor": t("g_sensor")},
    )
    return fig


def grafico_provincias(df):
    """Detecciones por provincia."""
    c = (df.groupby("provincia", observed=True).size()
         .reset_index(name="detecciones").sort_values("detecciones"))
    return px.bar(c, x="detecciones", y="provincia", orientation="h",
                  title=t("g_t_prov"),
                  labels={"detecciones": t("g_det"), "provincia": t("g_provincia")},
                  height=max(350, 24 * len(c)))


ANIOS_SIN_DATO = (2005, 2010, 2016)  # vaciar con () cuando A1 entregue MODIS completo
# Las fases son claves internas (en español); lo que se ve sale de t(...)
COLORES_FASE = {"El Niño": "#d62728", "La Niña": "#1f77b4", "Neutro": "#9e9e9e"}
FASE_CLAVE = {"El Niño": "g_f_nino", "La Niña": "g_f_nina", "Neutro": "g_f_neutro"}
ORDEN_TRIM = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
              "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def _fase_txt(f):
    return t(FASE_CLAVE[f])


def cargar_oni(ruta="data/oni.txt", rezago=0):
    """Lee el índice de NOAA y clasifica cada mes en El Niño / La Niña / Neutro."""
    d = pd.read_csv(ruta, sep=r"\s+")
    if "SEAS" not in d.columns:
        raise ValueError("Unexpected format in oni.txt; check the first lines.")
    d = d[d["SEAS"].isin(ORDEN_TRIM)].reset_index(drop=True)
    valor = pd.to_numeric(d.iloc[:, -1], errors="coerce")
    centro = {s: i + 1 for i, s in enumerate(ORDEN_TRIM)}  # DJF -> enero, etc.
    out = pd.DataFrame({
        "fecha": pd.to_datetime(dict(
            year=pd.to_numeric(d["YR"]), month=d["SEAS"].map(centro), day=1)),
        "oni": valor,
    }).sort_values("fecha").reset_index(drop=True)

    out["fase"] = "Neutro"
    for signo, nombre in ((1, "El Niño"), (-1, "La Niña")):
        cond = (signo * out["oni"]) >= 0.5
        grupo = (cond != cond.shift()).cumsum()
        largo = cond.groupby(grupo).transform("sum")
        out.loc[cond & (largo >= 5), "fase"] = nombre

    if rezago:
        out["fecha"] = out["fecha"] + pd.DateOffset(months=rezago)
    return out


def _conteo_mensual(df):
    f = df["fecha"]
    n = f.groupby([f.dt.year.rename("anio"), f.dt.month.rename("mes")]).size()
    inicio = pd.to_datetime(pd.DataFrame({
        "year": n.index.get_level_values(0),
        "month": n.index.get_level_values(1),
        "day": 1,
    }))
    c = pd.Series(n.to_numpy().astype(float), index=pd.DatetimeIndex(inicio)).sort_index()
    c = c.reindex(pd.date_range(c.index.min(), c.index.max(), freq="MS"), fill_value=0)
    c[c.index.year.isin(ANIOS_SIN_DATO)] = float("nan")  # ausencia de dato, no cero
    return c.rename_axis("fecha").rename("detecciones").reset_index()


def grafico_enso_mensual(df, oni):
    """Serie mensual de detecciones con bandas de El Niño / La Niña."""
    c = _conteo_mensual(df)
    fig = px.line(c, x="fecha", y="detecciones", title=t("g_t_enso_m"),
                  labels={"fecha": t("g_fecha"), "detecciones": t("g_det")})
    o = oni[(oni["fecha"] >= c["fecha"].min()) & (oni["fecha"] <= c["fecha"].max())]
    o = o.reset_index(drop=True)
    grupo = (o["fase"] != o["fase"].shift()).cumsum()
    for _, tr in o.groupby(grupo):
        fase = tr["fase"].iloc[0]
        if fase == "Neutro":
            continue
        x1 = tr["fecha"].iloc[-1] + pd.DateOffset(months=1)
        fig.add_vrect(
            x0=tr["fecha"].iloc[0].strftime("%Y-%m-%d"), x1=x1.strftime("%Y-%m-%d"),
            fillcolor=COLORES_FASE[fase], opacity=0.18, line_width=0, layer="below",
        )
    for fase in ("El Niño", "La Niña"):  # leyenda de las bandas
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers", name=_fase_txt(fase),
            marker=dict(size=10, color=COLORES_FASE[fase])))
    fig.update_layout(height=420, legend_title_text="")
    return fig


def grafico_enso_fases(df, oni):
    """Actividad relativa por fase. 1 = lo típico para ese mes del año
    (así se descuenta la estacionalidad)."""
    c = _conteo_mensual(df).dropna().copy()
    c["mes"] = c["fecha"].dt.month
    c["indice"] = c["detecciones"] / c.groupby("mes")["detecciones"].transform("mean")
    c = c.merge(oni[["fecha", "fase"]], on="fecha", how="inner")
    n = c["fase"].value_counts()
    c["etiqueta"] = c["fase"].map(lambda f: t("g_etq_fase", fase=_fase_txt(f), n=n[f]))
    orden = [t("g_etq_fase", fase=_fase_txt(f), n=n[f])
             for f in ("El Niño", "Neutro", "La Niña") if f in n]
    fig = px.box(
        c, x="etiqueta", y="indice", color="fase", points="all",
        color_discrete_map=COLORES_FASE, category_orders={"etiqueta": orden},
        title=t("g_t_enso_f"),
        labels={"etiqueta": "", "indice": t("g_act_rel"), "fase": t("g_fase")},
    )
    fig.add_hline(y=1, line_dash="dash")
    fig.update_layout(showlegend=False, height=450)
    return fig