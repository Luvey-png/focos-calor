import plotly.express as px


def grafico_mensual(df):
    """Recibe el DataFrame filtrado y devuelve una figura de Plotly.
    A3 reemplaza el contenido de esta función; el nombre y lo que
    recibe/devuelve NO cambian, así app.py sigue funcionando."""
    d = df.copy()
    d["mes"] = d["fecha"].dt.to_period("M").astype(str)
    conteo = d.groupby(["mes", "sensor"]).size().reset_index(name="detecciones")
    fig = px.bar(
        conteo, x="mes", y="detecciones", color="sensor",
        barmode="group", title="Detecciones térmicas por mes y sensor",
    )
    return fig