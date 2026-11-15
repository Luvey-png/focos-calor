import base64
import types
from pathlib import Path
import plotly.express as px
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

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
.solo-movil { display:none; font-size:.85rem; opacity:.8; margin-bottom:.6rem; }
@media (max-width: 640px) {
  .block-container { padding:.6rem .6rem 3rem; }
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


def _plotly_en_espanol():
    """Todos los gráficos Plotly: coma decimal, punto de miles y sin sufijo 'k'."""
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
        "#FF6B1A", "#4DABF7", "#FFB347", "#69DB7C", "#F06595", "#B197FC"]
    _plotly_en_espanol()
    img = _b64(LOGO)
    if img:
        st.sidebar.markdown(
            f'<img class="sb-logo" src="data:image/png;base64,{img}" alt="{NOMBRE}">',
            unsafe_allow_html=True,
        )


def encabezado(df):
    img = _b64(LOGO)
    if img:
        marca = f'<img src="data:image/png;base64,{img}" alt="{NOMBRE}">'
        titulo = f'<div class="hero-s">{LEMA}</div>'
    else:
        marca = "<span style='font-size:2.4rem'>🔥</span>"
        titulo = f'<div class="hero-t">{NOMBRE}</div><div class="hero-s">{LEMA}</div>'
    f0, f1 = df["fecha"].min(), df["fecha"].max()
    nprov = df["provincia"].nunique()
    html = (
        f'<div class="hero">{marca}<div>{titulo}</div></div>'
        '<div class="kpis">'
        f'<div class="kpi"><b>{_miles(len(df))}</b><span>detecciones en la base</span></div>'
        f'<div class="kpi"><b>{f0:%Y}–{f1:%Y}</b><span>período cubierto</span></div>'
        f'<div class="kpi"><b>{f1:%d/%m/%Y}</b><span>último dato</span></div>'
        f'<div class="kpi"><b>{nprov}</b><span>provincias</span></div>'
        '</div>'
        '<div class="solo-movil">☰ Tocá la flecha de arriba a la izquierda para abrir los filtros.</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    st.warning(
        "⚠️ Un foco de calor NO es un incendio confirmado. Es una detección térmica "
        "satelital que puede tener otras causas. (Texto provisorio: Luis lo redacta.)"
    )