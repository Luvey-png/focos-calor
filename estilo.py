import base64
import re
import types
from pathlib import Path
import plotly.express as px
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from idioma import t

NOMBRE = "Igneus" 
LEMA = "Observatorio de detecciones térmicas de Argentina"
LOGO = Path("assets/imagotipo.png")
ICONO = Path("assets/icono.png")

CSS = """
:root { --fuego:#FF6B1A; --brasa:#FFB347; --ceniza:#1E1714; }
.block-container { padding-top: 1.2rem; max-width: 1250px; }
footer { visibility: hidden; }
.sb-logo { display:block; width:80%; max-width:220px; margin:.2rem 0 1rem; }
.hero { display:flex; align-items:center; gap:1.2rem; padding:1.1rem 1.4rem;
  border-radius:18px; margin-bottom:.8rem;
  background: linear-gradient(120deg,#2A130A 0%,#4A1E0B 55%,#7A2E0C 100%);
  border:1px solid rgba(255,140,60,.25); }
.hero img { height:88px; width:auto; }
.hero-t { font-size:2rem; font-weight:800; line-height:1.1; color:#FFF3E6; }
.hero-s { color:#FFD3A8; font-size:1.05rem; }
.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:.7rem; margin-bottom:1rem; }
.kpi { background:var(--ceniza); border:1px solid rgba(255,140,60,.18);
  border-radius:14px; padding:.7rem .9rem; }
.kpi b { display:block; font-size:1.35rem; color:var(--brasa); }
.kpi span { font-size:.78rem; opacity:.75; }
button[data-baseweb="tab"] { font-weight:600; }
[data-testid="stMetric"] { background:var(--ceniza); border-radius:12px;
  padding:.6rem .8rem; border:1px solid rgba(255,140,60,.15); }
.titulo-graf { font-weight:700; font-size:.98rem; line-height:1.3; margin:.8rem 0 .1rem; }
.solo-movil { display:none; font-size:.85rem; opacity:.8; margin-bottom:.6rem; }
@media (max-width: 640px) {
  .block-container { padding:3.4rem .7rem 3rem; }
  h2, [data-testid="stHeading"] h2 { font-size:1.25rem !important; }
  h3, [data-testid="stHeading"] h3 { font-size:1.08rem !important; }
  [data-testid="stAlert"] p, [data-testid="stCaptionContainer"] p { font-size:.85rem; }
  [data-testid="stMarkdownContainer"] p { overflow-wrap:anywhere; }
  [data-testid="stMetric"] { padding:.45rem .6rem; }
  [data-testid="stMetricValue"] { font-size:1.4rem; }
  [data-testid="stChatMessage"] { padding:.6rem .5rem; }
  .stButton button { width:100%; }
  .hero { padding:.8rem; gap:.8rem; border-radius:14px; }
  .hero img { height:56px; }
  .hero-t { font-size:1.35rem; }
  .hero-s { font-size:.85rem; }
  .kpis { grid-template-columns:repeat(2,1fr); }
  .kpi b { font-size:1.1rem; }
  button[data-baseweb="tab"] { padding:.4rem .6rem; font-size:.82rem; }
  .solo-movil { display:block; }
}
"""


def _b64(ruta):
    return base64.b64encode(ruta.read_bytes()).decode() if ruta.exists() else None


def _miles(n):
    return f"{n:,}".replace(",", ".")


def es_movil():
    """True si el navegador es de un celular o tablet (según el User-Agent)."""
    if "_es_movil" not in st.session_state:
        try:
            ua = st.context.headers.get("User-Agent", "") or ""
        except Exception:
            ua = ""
        st.session_state["_es_movil"] = bool(
            re.search(r"Mobi|Android|iPhone|iPod|iPad|Opera Mini|IEMobile", ua))
    return st.session_state["_es_movil"]


def ajustar_para_movil(fig):
    """Adapta un gráfico Plotly a una pantalla de celular: saca el título (se
    muestra aparte, como texto que se acomoda solo), pone la leyenda y la barra
    de colores arriba del gráfico (así no le quitan ancho), achica márgenes y letra.
    Devuelve el título que tenía el gráfico."""
    titulo = fig.layout.title.text
    fig.update_layout(title_text="")
    con_color = bool(fig.layout.coloraxis.colorscale) or any(
        t.type == "heatmap" for t in fig.data)
    nombres = {t.name for t in fig.data if t.name and t.showlegend is not False}
    con_leyenda = fig.layout.showlegend is not False and len(nombres) > 1 and not con_color
    es_mapa = bool(fig.layout.map and fig.layout.map.style)
    extra = (48 if con_color else 0) + (34 if con_leyenda else 0)
    fig.update_layout(
        font=dict(size=11),
        margin=dict(l=6, r=6, t=extra + 8, b=6),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, xanchor="left",
                    font=dict(size=10), title_text=""),
    )
    if not es_mapa:
        fig.update_xaxes(automargin=True, title_font=dict(size=11), tickfont=dict(size=10))
        fig.update_yaxes(automargin=True, title_font=dict(size=11), tickfont=dict(size=10))
    barra = dict(orientation="h", yanchor="bottom", y=1.02, x=0, xanchor="left", len=1,
                 thickness=10, title_side="top", title_font=dict(size=10),
                 tickfont=dict(size=9))
    fig.update_coloraxes(colorbar=barra)
    fig.update_traces(colorbar=barra, selector=dict(type="heatmap"))
    for an in fig.layout.annotations or []:
        an.font.size = 9
    return titulo


def _plotly_en_espanol():
    """Todos los gráficos Plotly: coma decimal, punto de miles y sin sufijo 'k'.
    En celulares, además, los adapta a pantallas angostas."""
    if getattr(DeltaGenerator.plotly_chart, "_es", False):
        return
    original = DeltaGenerator.plotly_chart

    def plotly_es(self, figure_or_data, *args, **kwargs):
        try:
            figure_or_data.update_layout(separators=",.")
            figure_or_data.update_yaxes(exponentformat="none")
            figure_or_data.update_coloraxes(colorbar_exponentformat="none")
            figure_or_data.update_traces(
                colorbar_exponentformat="none", selector=dict(type="heatmap"))
        except Exception:
            pass
        if es_movil():
            try:
                titulo = ajustar_para_movil(figure_or_data)
                if titulo:
                    self.markdown(f'<div class="titulo-graf">{titulo}</div>',
                                  unsafe_allow_html=True)
            except Exception:
                pass
            config = dict(kwargs.pop("config", None) or {})
            config.setdefault("displayModeBar", False)
            config.setdefault("scrollZoom", False)
            kwargs["config"] = config
        return original(self, figure_or_data, *args, **kwargs)

    plotly_es._es = True
    DeltaGenerator.plotly_chart = plotly_es
    try:
        st.plotly_chart = types.MethodType(plotly_es, st._main)
    except Exception:
        pass


def aplicar_estilo():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
    px.defaults.color_discrete_sequence = [
        "#E41AFF", "#11ECFC", "#FFB347", "#69DB7C", "#F06595", "#B197FC"]
    _plotly_en_espanol()
    img = _b64(LOGO)
    if img:
        st.sidebar.markdown(
            f'<img class="sb-logo" src="data:image/png;base64,{img}" alt="{NOMBRE}">',
            unsafe_allow_html=True,
        )


def encabezado(df):
    es = st.session_state.get("idioma", "es") == "es"
    img = _b64(LOGO)
    lema = t("lema")
    if img:
        marca = f'<img src="data:image/png;base64,{img}" alt="{NOMBRE}">'
        titulo = f'<div class="hero-s">{lema}</div>'
    else:
        marca = ""
        titulo = f'<div class="hero-t">{NOMBRE}</div><div class="hero-s">{lema}</div>'
    f0, f1 = df["fecha"].min(), df["fecha"].max()
    nprov = df["provincia"].nunique()
    total = _miles(len(df)) if es else f"{len(df):,}"
    ultimo = f"{f1:%d/%m/%Y}" if es else f"{f1:%Y-%m-%d}"
    html = (
        f'<div class="hero">{marca}<div>{titulo}</div></div>'
        '<div class="kpis">'
        f'<div class="kpi"><b>{total}</b><span>{t("kpi_det")}</span></div>'
        f'<div class="kpi"><b>{f0:%Y}–{f1:%Y}</b><span>{t("kpi_periodo")}</span></div>'
        f'<div class="kpi"><b>{ultimo}</b><span>{t("kpi_ultimo")}</span></div>'
        f'<div class="kpi"><b>{nprov}</b><span>{t("kpi_prov")}</span></div>'
        '</div>'
        f'<div class="solo-movil">{t("movil")}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    st.warning(t("aviso_corto"))
    with st.expander(t("aviso_ver")):
        st.markdown(t("aviso_largo"))