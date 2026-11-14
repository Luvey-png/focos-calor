import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def grafico_mensual(df):
    """Detecciones por mes y sensor. A3 puede reemplazar el contenido;
    el nombre y lo que recibe/devuelve NO cambian."""
    mes = df["fecha"].dt.to_period("M").dt.to_timestamp()
    conteo = (
        df.assign(mes=mes)
        .groupby(["mes", "sensor"], observed=True)
        .size()
        .reset_index(name="detecciones")
    )
    return px.line(
        conteo, x="mes", y="detecciones", color="sensor",
        title="Detecciones térmicas por mes y sensor",
    )


def grafico_calendario(df, anio):
    """Calendario diario de un año: un cuadrado por día."""
    d = df[df["fecha"].dt.year == anio]
    por_dia = d.groupby("fecha").size()
    dias = pd.date_range(f"{anio}-01-01", f"{anio}-12-31")
    por_dia = por_dia.reindex(dias, fill_value=0)

    c = por_dia.rename("detecciones").rename_axis("fecha").reset_index()
    offset = dias[0].weekday()
    c["semana"] = (c["fecha"].dt.dayofyear - 1 + offset) // 7
    c["dia_sem"] = c["fecha"].dt.weekday
    c["texto"] = c["fecha"].dt.strftime("%d/%m/%Y")

    z = c.pivot(index="dia_sem", columns="semana", values="detecciones")
    t = c.pivot(index="dia_sem", columns="semana", values="texto")

    fig = go.Figure(go.Heatmap(
        z=z.values, x=z.columns, y=list(range(7)),
        customdata=t.values,
        hovertemplate="%{customdata}<br>%{z} detecciones<extra></extra>",
        colorscale="YlOrRd", xgap=2, ygap=2,
        colorbar=dict(title="Detecciones"),
    ))
    # etiquetas de mes sobre el eje X (semana en que empieza cada mes)
    inicio_mes = c[c["fecha"].dt.day == 1]
    fig.update_xaxes(
        tickvals=inicio_mes["semana"].tolist(),
        ticktext=[MESES[m - 1] for m in inicio_mes["fecha"].dt.month],
        showgrid=False,
    )
    fig.update_yaxes(
        tickvals=list(range(7)), ticktext=DIAS,
        autorange="reversed", showgrid=False,
    )
    fig.update_layout(
        title=f"Calendario de detecciones térmicas {anio}",
        height=300, margin=dict(l=40, r=20, t=60, b=30),
    )
    return fig


def grafico_anio_mes(df):
    """Mapa de calor: filas = años, columnas = meses."""
    d = pd.DataFrame({"anio": df["fecha"].dt.year, "mes": df["fecha"].dt.month})
    t = d.groupby(["anio", "mes"]).size().unstack(fill_value=0)
    t = t.reindex(columns=range(1, 13), fill_value=0)
    fig = px.imshow(
        t.values, x=MESES, y=t.index.astype(str),
        color_continuous_scale="YlOrRd", aspect="auto",
        labels=dict(x="Mes", y="Año", color="Detecciones"),
        title="Actividad térmica por año y mes",
    )
    fig.update_layout(height=max(350, 22 * len(t)))
    return fig

def grafico_comparacion_sensores(df):
    """MODIS vs VIIRS: detecciones por año, una barra por sensor."""
    d = pd.DataFrame({"anio": df["fecha"].dt.year, "sensor": df["sensor"].astype(str)})
    conteo = d.groupby(["anio", "sensor"]).size().reset_index(name="detecciones")
    fig = px.bar(
        conteo, x="anio", y="detecciones", color="sensor", barmode="group",
        title="Detecciones por año y sensor",
        labels={"anio": "Año", "detecciones": "Detecciones"},
    )
    fig.update_xaxes(dtick=1)
    return fig


def grafico_estacionalidad(df):
    """Detecciones por mes del año (todos los años juntos), por sensor.
    Muestra en qué época del año hay más actividad."""
    d = pd.DataFrame({"mes": df["fecha"].dt.month, "sensor": df["sensor"].astype(str)})
    conteo = d.groupby(["mes", "sensor"]).size().reset_index(name="detecciones")
    conteo["mes_nombre"] = conteo["mes"].map(lambda m: MESES[m - 1])
    fig = px.line(
        conteo, x="mes_nombre", y="detecciones", color="sensor", markers=True,
        category_orders={"mes_nombre": MESES},
        title="Estacionalidad: detecciones por mes del año",
        labels={"mes_nombre": "Mes", "detecciones": "Detecciones"},
    )
    return fig

def grafico_confianza(df):
    """Distribución de confianza por sensor (en porcentaje)."""
    d = pd.DataFrame({
        "sensor": df["sensor"].astype(str),
        "confianza": df["confianza"].astype(str),
    })
    conteo = d.groupby(["sensor", "confianza"]).size().reset_index(name="n")
    conteo["porcentaje"] = conteo["n"] / conteo.groupby("sensor")["n"].transform("sum") * 100
    fig = px.bar(
        conteo, x="sensor", y="porcentaje", color="confianza",
        category_orders={"confianza": ["baja", "nominal", "alta", "desconocida"]},
        title="Distribución de confianza por sensor (%)",
        labels={"porcentaje": "% de detecciones"},
    )
    return fig

def grafico_provincias(df):
    """Detecciones por provincia."""
    c = (df.groupby("provincia", observed=True).size()
         .reset_index(name="detecciones").sort_values("detecciones"))
    return px.bar(c, x="detecciones", y="provincia", orientation="h",
                  title="Detecciones térmicas por provincia",
                  height=max(350, 24 * len(c)))

ANIOS_SIN_DATO = (2005, 2010, 2016)  # vaciar con () cuando A1 entregue MODIS completo
COLORES_FASE = {"El Niño": "#d62728", "La Niña": "#1f77b4", "Neutro": "#9e9e9e"}
ORDEN_TRIM = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
              "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def cargar_oni(ruta="data/oni.txt", rezago=0):
    """Lee el índice de NOAA y clasifica cada mes en El Niño / La Niña / Neutro."""
    d = pd.read_csv(ruta, sep=r"\s+")
    if "SEAS" not in d.columns:
        raise ValueError("Formato inesperado en oni.txt; revisá las primeras líneas.")
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
    mes = df["fecha"].dt.to_period("M").dt.to_timestamp()
    c = mes.value_counts().sort_index().astype(float)
    c = c.reindex(pd.date_range(c.index.min(), c.index.max(), freq="MS"), fill_value=0)
    c[c.index.year.isin(ANIOS_SIN_DATO)] = float("nan")  # ausencia de dato, no cero
    return c.rename_axis("fecha").rename("detecciones").reset_index()


def grafico_enso_mensual(df, oni):
    """Serie mensual de detecciones con bandas de El Niño / La Niña."""
    c = _conteo_mensual(df)
    fig = px.line(c, x="fecha", y="detecciones",
                  title="Detecciones mensuales y fases de El Niño / La Niña")
    o = oni[(oni["fecha"] >= c["fecha"].min()) & (oni["fecha"] <= c["fecha"].max())]
    o = o.reset_index(drop=True)
    grupo = (o["fase"] != o["fase"].shift()).cumsum()
    for _, t in o.groupby(grupo):
        fase = t["fase"].iloc[0]
        if fase == "Neutro":
            continue
        x1 = t["fecha"].iloc[-1] + pd.DateOffset(months=1)
        fig.add_vrect(
            x0=t["fecha"].iloc[0].strftime("%Y-%m-%d"), x1=x1.strftime("%Y-%m-%d"),
            fillcolor=COLORES_FASE[fase], opacity=0.18, line_width=0, layer="below",
        )
    for fase in ("El Niño", "La Niña"):  # leyenda de las bandas
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers", name=fase,
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
    c["etiqueta"] = c["fase"].map(lambda f: f"{f} (n={n[f]} meses)")
    orden = [f"{f} (n={n[f]} meses)" for f in ("El Niño", "Neutro", "La Niña") if f in n]
    fig = px.box(
        c, x="etiqueta", y="indice", color="fase", points="all",
        color_discrete_map=COLORES_FASE, category_orders={"etiqueta": orden},
        title="Actividad relativa según la fase (1 = típico para ese mes)",
        labels={"etiqueta": "", "indice": "Actividad relativa"},
    )
    fig.add_hline(y=1, line_dash="dash")
    fig.update_layout(showlegend=False, height=450)
    return fig