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