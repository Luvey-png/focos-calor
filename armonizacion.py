"""Armonización de la serie de detecciones entre satélites (MODIS y VIIRS).

Problema: cada vez que entra un satélite nuevo cambia la cantidad de detecciones,
aunque la actividad real no cambie:
  - 2000-2001: solo MODIS Terra
  - 2002: se suma MODIS Aqua
  - 2012: se suma VIIRS S-NPP (375 m, ~5 veces más detecciones que MODIS)
  - 2018: se suma VIIRS NOAA-20 (duplica los conteos de VIIRS)
  - 2023: se suma VIIRS NOAA-21
Sumar todo genera saltos artificiales.

Método: llevar todo a una escala común, "equivalente VIIRS S-NPP".
  1. 2012 en adelante: se usa lo observado por VIIRS S-NPP (un solo satélite,
     serie consistente).
  2. 2002-2011: se estima S-NPP a partir de MODIS Aqua. Aqua y S-NPP pasan a la
     misma hora (~13:30 local), así que ven el mismo ciclo diario del fuego.
     El factor S-NPP/Aqua se calcula por provincia y mes del año con los años en
     que funcionan los dos (2012-2025), porque cambia según el tipo de fuego y la
     estación.
  3. 2000-2001: solo hay Terra. Se lleva Terra a Aqua (factor Aqua/Terra por
     provincia y mes, 2002-2025) y después a S-NPP.
  Los años sin ningún dato quedan vacíos (no se inventan).
Validación: se ajustan los factores con 2012-2018 y se predice S-NPP 2019-2025
a partir de Aqua, años que el método no vio.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

SAT_REF = "N"        # VIIRS S-NPP en la columna 'satelite'
SAT_PUENTE = "Aqua"  # MODIS Aqua
SAT_VIEJO = "Terra"  # MODIS Terra
MIN_DET = 20         # mínimo de detecciones del satélite puente para confiar en un factor local
LANZAMIENTOS = {2002: "Aqua", 2012: "VIIRS S-NPP", 2018: "NOAA-20", 2023: "NOAA-21"}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# ---------- Tabla base ----------
def tabla_mensual(df):
    """Conteos por año, mes, provincia y satélite (sin quitar duplicados:
    cada satélite se cuenta por separado)."""
    d = pd.DataFrame({
        "anio": df["fecha"].dt.year.astype("int16"),
        "mes": df["fecha"].dt.month.astype("int8"),
        "provincia": df["provincia"].astype(str),
        "satelite": df["satelite"].astype(str),
    })
    m = d.groupby(["anio", "mes", "provincia", "satelite"]).size().unstack("satelite", fill_value=0)
    for s in (SAT_REF, SAT_PUENTE, SAT_VIEJO):
        if s not in m.columns:
            m[s] = 0
    # disponibilidad de cada satélite por año y mes (a nivel país)
    disp = d.groupby(["anio", "mes", "satelite"]).size().unstack("satelite", fill_value=0) > 0
    for s in (SAT_REF, SAT_PUENTE, SAT_VIEJO):
        if s not in disp.columns:
            disp[s] = False
    # grilla completa: un mes sin detecciones en una provincia es un cero real
    # si el satélite estaba funcionando ese mes
    provs = sorted(d["provincia"].unique())
    idx = pd.MultiIndex.from_product(
        [disp.index.get_level_values(0).unique(), range(1, 13), provs],
        names=["anio", "mes", "provincia"])
    m = m.reindex(idx, fill_value=0).reset_index()
    m = m.join(disp[[SAT_REF, SAT_PUENTE, SAT_VIEJO]].add_prefix("hay_"), on=["anio", "mes"])
    for s in (SAT_REF, SAT_PUENTE, SAT_VIEJO):
        m[f"hay_{s}"] = m[f"hay_{s}"].fillna(False).astype(bool)
    return m


# ---------- Factores ----------
def _factor(m, num, den, anios):
    """Factor num/den por provincia y mes, con respaldo por provincia y nacional."""
    t = m[m["anio"].isin(anios) & m[f"hay_{num}"] & m[f"hay_{den}"]]
    pm = t.groupby(["provincia", "mes"])[[num, den]].sum()
    local = (pm[num] / pm[den]).where(pm[den] >= MIN_DET)
    p = t.groupby("provincia")[[num, den]].sum()
    prov = (p[num] / p[den]).where(p[den] >= MIN_DET)
    nac = t[num].sum() / max(t[den].sum(), 1)
    return local, prov, nac


def _aplicar(m, factor):
    local, prov, nac = factor
    r = pd.Series(list(zip(m["provincia"], m["mes"]))).map(local.to_dict())
    r.index = m.index
    r = r.fillna(m["provincia"].map(prov)).fillna(nac)
    return r


def anios_completos(m, *sats):
    """Años en que todos esos satélites tienen datos los 12 meses (deja afuera el
    año en curso, que viene de datos de casi tiempo real e incompletos)."""
    ok = m.groupby("anio")[[f"hay_{s}" for s in sats]].all().all(axis=1)
    return sorted(ok[ok].index)


def ajustar(m, anios_ref=None, anios_terra=None):
    if anios_ref is None:
        anios_ref = anios_completos(m, SAT_REF, SAT_PUENTE)
    if anios_terra is None:
        anios_terra = anios_completos(m, SAT_PUENTE, SAT_VIEJO)
    return {
        "ref_aqua": _factor(m, SAT_REF, SAT_PUENTE, anios_ref),
        "aqua_terra": _factor(m, SAT_PUENTE, SAT_VIEJO, anios_terra),
    }


def armonizar(m, factores=None):
    """Agrega 'armonizado' (equivalente VIIRS S-NPP) y 'metodo' a la tabla mensual."""
    if factores is None:
        factores = ajustar(m)
    m = m.copy()
    r_ra = _aplicar(m, factores["ref_aqua"])
    r_at = _aplicar(m, factores["aqua_terra"])
    m["armonizado"] = np.select(
        [m[f"hay_{SAT_REF}"], m[f"hay_{SAT_PUENTE}"], m[f"hay_{SAT_VIEJO}"]],
        [m[SAT_REF], m[SAT_PUENTE] * r_ra, m[SAT_VIEJO] * r_at * r_ra],
        default=np.nan,
    )
    m["metodo"] = np.select(
        [m[f"hay_{SAT_REF}"], m[f"hay_{SAT_PUENTE}"], m[f"hay_{SAT_VIEJO}"]],
        ["Observado (VIIRS S-NPP)", "Estimado desde MODIS Aqua", "Estimado desde MODIS Terra"],
        default="Sin datos",
    )
    sats = [c for c in m.columns if c not in ("anio", "mes", "provincia", "armonizado", "metodo")
            and not c.startswith("hay_")]
    m["suma_cruda"] = m[sats].sum(axis=1)
    return m


# ---------- Validación ----------
def validar(m, corte=2018):
    """Ajusta con 2012..corte y predice S-NPP en los años siguientes desde Aqua."""
    ok = m[m["anio"].isin(anios_completos(m, SAT_REF, SAT_PUENTE))]
    entren = ok[ok["anio"] <= corte]
    prueba = ok[ok["anio"] > corte].copy()
    f = _factor(entren, SAT_REF, SAT_PUENTE, entren["anio"].unique())
    prueba["pred_local"] = prueba[SAT_PUENTE] * _aplicar(prueba, f)
    prueba["pred_unico"] = prueba[SAT_PUENTE] * f[2]
    prueba["suma_cruda"] = prueba[[c for c in ("Aqua", "Terra", "N", "N20", "N21") if c in prueba]].sum(axis=1)

    def errores(nivel, minimo):
        g = prueba.groupby(nivel)[[SAT_REF, "pred_local", "pred_unico", "suma_cruda"]].sum()
        g = g[g[SAT_REF] >= minimo]
        return {k: float((abs(g[k] - g[SAT_REF]) / g[SAT_REF]).median())
                for k in ("pred_local", "pred_unico", "suma_cruda")}

    e_mes = errores(["anio", "mes"], 100)
    e_prov = errores(["anio", "provincia"], 200)
    tabla = pd.DataFrame({
        "Método": ["Factor por provincia y mes (el nuestro)", "Factor único nacional",
                   "Sumar todos los satélites (sin armonizar)"],
        "Error mensual país": [e_mes["pred_local"], e_mes["pred_unico"], e_mes["suma_cruda"]],
        "Error anual por provincia": [e_prov["pred_local"], e_prov["pred_unico"], e_prov["suma_cruda"]],
    })
    serie = prueba.groupby(["anio", "mes"])[[SAT_REF, "pred_local", "pred_unico"]].sum().reset_index()
    serie["fecha"] = pd.to_datetime(dict(year=serie["anio"], month=serie["mes"], day=1))
    return tabla, serie, corte


# ---------- Resúmenes para la app ----------
def filtrar(h, provincias, desde, hasta):
    return h[h["provincia"].isin(provincias) & h["anio"].between(desde.year, hasta.year)]


def anual(h):
    a = h.groupby("anio").agg(armonizado=("armonizado", lambda s: s.sum(min_count=1)),
                              suma_cruda=("suma_cruda", "sum"))
    # un año sin datos de ningún satélite queda vacío
    sin = h.groupby("anio")["metodo"].apply(lambda s: (s == "Sin datos").all())
    a.loc[sin, ["armonizado", "suma_cruda"]] = np.nan
    # los años que faltan por completo aparecen vacíos (cortan la línea)
    a = a.reindex(range(int(a.index.min()), int(a.index.max()) + 1))
    a.index.name = "anio"
    return a.reset_index()


def mensual_total(h):
    g = h.groupby(["anio", "mes"]).agg(armonizado=("armonizado", lambda s: s.sum(min_count=1)),
                                       metodo=("metodo", "first")).reset_index()
    g["fecha"] = pd.to_datetime(dict(year=g["anio"], month=g["mes"], day=1))
    return g


def anomalias(h, umbral=1.5):
    g = mensual_total(h).dropna(subset=["armonizado"])
    clima = g.groupby("mes")["armonizado"].agg(["mean", "std"])
    g = g.join(clima, on="mes")
    g["z"] = (g["armonizado"] - g["mean"]) / g["std"].replace(0, np.nan)
    g["anomalo"] = g["z"] >= umbral
    return g


# ---------- Gráficos ----------
def grafico_antes_despues(a, anio_parcial=None):
    fig = go.Figure()
    fig.add_bar(x=a["anio"], y=a["suma_cruda"], name="Suma cruda de todos los satélites",
                marker_color="rgba(160,160,160,0.45)")
    fig.add_scatter(x=a["anio"], y=a["armonizado"], name="Serie armonizada (equivalente VIIRS S-NPP)",
                    mode="lines+markers", line=dict(color="#FF6B1A", width=3), connectgaps=False)
    for anio, sat in LANZAMIENTOS.items():
        fig.add_vline(x=anio - 0.5, line_dash="dot", line_color="#999")
        fig.add_annotation(x=anio - 0.5, y=1.02, yref="paper", text=f"+{sat}",
                           showarrow=False, font=dict(size=10), xanchor="left")
    if anio_parcial is not None and anio_parcial in set(a["anio"]):
        fig.add_annotation(x=anio_parcial, y=0, yref="paper", yanchor="bottom", text="año en curso<br>(incompleto)",
                           showarrow=False, font=dict(size=9, color="#bbb"))
    fig.update_layout(title="Antes y después: sumar satélites vs. serie armonizada",
                      xaxis_title="Año", yaxis_title="Detecciones por año",
                      legend=dict(orientation="h", y=-0.2), height=470)
    return fig


def grafico_calendario_armonizado(h):
    g = mensual_total(h)
    t = g.pivot(index="anio", columns="mes", values="armonizado").reindex(columns=range(1, 13))
    t = t.reindex(range(int(t.index.min()), int(t.index.max()) + 1))
    fig = px.imshow(t, x=MESES, y=t.index.astype(str), aspect="auto",
                    color_continuous_scale="YlOrRd",
                    labels=dict(x="Mes", y="Año", color="Detecciones (eq. S-NPP)"),
                    title="Calendario armonizado de actividad de quema")
    fig.update_layout(height=max(420, 22 * len(t)))
    return fig


def grafico_periodos_criticos(h):
    g = mensual_total(h).dropna(subset=["armonizado"])
    c = g.groupby("mes")["armonizado"].agg(["mean", "std"]).reindex(range(1, 13)).reset_index()
    umbral = c["mean"].quantile(0.75)
    c["tipo"] = np.where(c["mean"] >= umbral, "Período crítico", "Resto del año")
    c["nombre_mes"] = c["mes"].map(lambda i: MESES[i - 1])
    fig = px.bar(c, x="nombre_mes", y="mean", color="tipo", category_orders={"nombre_mes": MESES},
                 error_y="std", color_discrete_map={"Período crítico": "#E8590C", "Resto del año": "#6c5f57"},
                 labels={"nombre_mes": "Mes", "mean": "Promedio armonizado", "tipo": ""},
                 title="Períodos críticos: actividad promedio de cada mes (armonizada)")
    return fig


def grafico_anomalias_armonizadas(g, umbral):
    fig = go.Figure()
    fig.add_scatter(x=g["fecha"], y=g["armonizado"], mode="lines", name="Armonizado",
                    line=dict(color="#c9b8aa"))
    fig.add_scatter(x=g["fecha"], y=g["mean"], mode="lines", name="Normal para ese mes",
                    line=dict(color="#888", dash="dot"))
    a = g[g["anomalo"]]
    fig.add_scatter(x=a["fecha"], y=a["armonizado"], mode="markers", name=f"Atípico (≥ {umbral} desvíos)",
                    marker=dict(color="#FF3B1A", size=9))
    fig.update_layout(title="Condiciones fuera de lo normal (sobre la serie armonizada)",
                      yaxis_title="Detecciones por mes (eq. S-NPP)", height=420,
                      legend=dict(orientation="h", y=-0.2))
    return fig


def grafico_validacion(serie, corte):
    fig = go.Figure()
    fig.add_scatter(x=serie["fecha"], y=serie[SAT_REF], name="VIIRS S-NPP observado",
                    line=dict(color="#F4EDE4", width=3))
    fig.add_scatter(x=serie["fecha"], y=serie["pred_local"], name="Estimado: factor por provincia y mes",
                    line=dict(color="#FF6B1A", dash="dash"))
    fig.add_scatter(x=serie["fecha"], y=serie["pred_unico"], name="Estimado: factor único nacional",
                    line=dict(color="#8a7f77", dash="dot"))
    fig.update_layout(title=f"Validación: años {corte + 1} en adelante, que el método no usó para ajustarse",
                      yaxis_title="Detecciones por mes", height=420, legend=dict(orientation="h", y=-0.2))
    return fig


def tabla_factores(m, provincias):
    local, prov, nac = ajustar(m)["ref_aqua"]
    t = local.unstack("mes").reindex(columns=range(1, 13))
    t.columns = MESES
    t = t.loc[t.index.isin(provincias)]
    t.insert(0, "Todo el año", prov.reindex(t.index))
    return t.round(1), nac
