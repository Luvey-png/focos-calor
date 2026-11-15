import streamlit as st

TEXTOS = {
    "es": {
        "tab_mapa": "Mapa",
        "tab_cerca": "Cerca de mí",
        "tab_arm": "Armonización",
        "tab_ia": "Asistente IA",
        "tab_graf": "Gráficos",
        "tab_cal": "Calendario",
        "tab_enso": "El Niño / La Niña",
        "tab_gases": "Gases de carbono",
        "tab_origen": "Origen (inferido)",
        "tab_quemas": "Quemas",
        "tab_metodo": "Método y fuentes",
        "tab_datos": "Datos",
        "prueba": "Estás viendo datos de PRUEBA, no datos reales.",
        "filtros": "Filtros",
        "quitar_dup": "Quitar duplicados entre sensores",
        "quitar_dup_help": "Une las detecciones de MODIS y VIIRS en el mismo lugar y día. La armonización de la serie entre satélites está en la pestaña 'Armonización'.",
        "sensor": "Sensor",
        "rango": "Rango de fechas",
        "toda_arg": "Toda Argentina",
        "region": "Región",
        "provincia": "Provincia",
        "tramo": "Hay un tramo de {dias} días sin datos en la base. Los conteos de ese período no son confiables.",
        "det_mostradas": "Detecciones mostradas: **{n}** de {total}",
        "sin_det": "No hay detecciones con esos filtros.",
        "lema": "Observatorio de detecciones térmicas de Argentina",
        "kpi_det": "detecciones en la base",
        "kpi_periodo": "período cubierto",
        "kpi_ultimo": "último dato",
        "kpi_prov": "provincias",
        "movil": "Tocá la flecha de arriba a la izquierda para abrir los filtros. Deslizá las pestañas hacia el costado para ver todas.",
        "aviso_corto": "Un foco de calor es una anomalía térmica detectada desde el espacio, no un incendio confirmado. IGNEUS analiza patrones históricos (2000–2026) y no predice eventos futuros.",
        "aviso_ver": "Ver aviso científico completo",
        "aviso_largo": "Un foco de calor (anomalía térmica infrarroja detectada desde el espacio) no equivale a un incendio forestal confirmado en terreno. Se filtraron los registros descartando volcanes, industrias y fuentes fijas para conservar exclusivamente la categoría estándar FIRMS de presunta vegetación bajo validación científica (type == 0) que aplica al catálogo Archive (2000–2025), ya que el tramo NRT reciente de 2026 no trae clasificación de tipo de fuente. Asimismo, los sensores satelitales no pueden distinguir de forma automatizada entre un incendio silvestre descontrolado y una quema agrícola autorizada. IGNEUS analiza patrones estadísticos e históricos (2000–2026), pero no realiza predicciones de eventos futuros.",
    },
    "en": {
        "tab_mapa": "Map",
        "tab_cerca": "Near me",
        "tab_arm": "Harmonization",
        "tab_ia": "AI Assistant",
        "tab_graf": "Charts",
        "tab_cal": "Calendar",
        "tab_enso": "El Niño / La Niña",
        "tab_gases": "Carbon gases",
        "tab_origen": "Origin (inferred)",
        "tab_quemas": "Controlled burns",
        "tab_metodo": "Method and sources",
        "tab_datos": "Data",
        "prueba": "You are viewing TEST data, not real data.",
        "filtros": "Filters",
        "quitar_dup": "Remove duplicates between sensors",
        "quitar_dup_help": "Merges MODIS and VIIRS detections at the same place and day. Harmonization of the series across satellites is in the 'Harmonization' tab.",
        "sensor": "Sensor",
        "rango": "Date range",
        "toda_arg": "All of Argentina",
        "region": "Region",
        "provincia": "Province",
        "tramo": "There is a {dias}-day gap with no data in the database. Counts for that period are not reliable.",
        "det_mostradas": "Detections shown: **{n}** of {total}",
        "sin_det": "No detections match these filters.",
        "lema": "Thermal detection observatory of Argentina",
        "kpi_det": "detections in the database",
        "kpi_periodo": "period covered",
        "kpi_ultimo": "latest data",
        "kpi_prov": "provinces",
        "movil": "Tap the arrow at the top left to open the filters. Swipe the tabs sideways to see them all.",
        "aviso_corto": "A heat hotspot is a thermal anomaly detected from space, not a confirmed wildfire. IGNEUS analyzes historical patterns (2000–2026) and does not predict future events.",
        "aviso_ver": "Read the full scientific notice",
        "aviso_largo": "A heat hotspot (an infrared thermal anomaly detected from space) is not the same as a wildfire confirmed on the ground. Records were filtered to discard volcanoes, industry and other fixed sources, keeping only the standard FIRMS category of presumed vegetation under scientific validation (type == 0), which applies to the Archive catalog (2000–2025), since the recent 2026 NRT segment carries no source-type classification. Likewise, satellite sensors cannot automatically tell an uncontrolled wildfire from an authorized agricultural burn. IGNEUS analyzes statistical and historical patterns (2000–2026), but does not forecast future events.",
    },
}


def selector_idioma():
    st.sidebar.radio(
        "Idioma / Language",
        ["es", "en"],
        format_func=lambda x: {"es": "Español", "en": "English"}[x],
        horizontal=True,
        key="idioma",
    )


def t(clave, **kw):
    idioma = st.session_state.get("idioma", "es")
    texto = TEXTOS.get(idioma, {}).get(clave) or TEXTOS["es"].get(clave, clave)
    return texto.format(**kw) if kw else texto

TEXTOS["es"].update({
    "modo_recientes": "Más recientes",
    "modo_aleatoria": "Muestra aleatoria",
    "mapa_titulo": "Mapa de detecciones térmicas",
    "mapa_modo": "Qué puntos mostrar",
    "mapa_max": "Cantidad máxima de puntos",
    "mapa_nota": "Se muestran {n} de {total} detecciones ({modo}). Los gráficos y conteos usan TODAS las detecciones filtradas. Acotá fechas o provincia para ver todos los puntos en el mapa.",
    "col_fecha": "Fecha",
    "col_confianza": "Confianza",
    "cal_titulo": "Calendario de actividad térmica",
    "cal_anio": "Año",
    "cal_nota": "Cada valor es un conteo de detecciones térmicas, no de incendios confirmados.",
})

TEXTOS["en"].update({
    "modo_recientes": "Most recent",
    "modo_aleatoria": "Random sample",
    "mapa_titulo": "Map of thermal detections",
    "mapa_modo": "Which points to show",
    "mapa_max": "Maximum number of points",
    "mapa_nota": "Showing {n} of {total} detections ({modo}). Charts and counts use ALL the filtered detections. Narrow the dates or province to see every point on the map.",
    "col_fecha": "Date",
    "col_confianza": "Confidence",
    "cal_titulo": "Thermal activity calendar",
    "cal_anio": "Year",
    "cal_nota": "Each value is a count of thermal detections, not confirmed wildfires.",
})

REGIONES_EN = {"Noreste": "Northeast", "Pampeana": "Pampas", "Noroeste": "Northwest",
               "Cuyo": "Cuyo", "Patagonia": "Patagonia"}


def region_txt(x):
    if st.session_state.get("idioma", "es") == "en":
        return REGIONES_EN.get(x, x)
    return x


def num(n):
    s = f"{n:,}"
    return s if st.session_state.get("idioma", "es") == "en" else s.replace(",", ".")


def formato_fecha():
    return "YYYY/MM/DD" if st.session_state.get("idioma", "es") == "en" else "DD/MM/YYYY"