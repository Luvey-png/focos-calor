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
        ["en", "es"],
        format_func=lambda x: {"es": "Español", "en": "English"}[x],
        horizontal=True,
        key="idioma",
    )


def t(clave, **kw):
    idioma = st.session_state.get("idioma", "en")
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
    if st.session_state.get("idioma", "en") == "en":
        return REGIONES_EN.get(x, x)
    return x


def num(n):
    s = f"{n:,}"
    return s if st.session_state.get("idioma", "en") == "en" else s.replace(",", ".")


def formato_fecha():
    return "YYYY/MM/DD" if st.session_state.get("idioma", "en") == "en" else "DD/MM/YYYY"

def fecha_txt(d):
    return f"{d:%Y-%m-%d}" if st.session_state.get("idioma", "en") == "en" else f"{d:%d/%m/%Y}"


SENALES_EN = {
    "Temporada habitual de quemas (jul-oct)": "Usual burning season (Jul-Oct)",
    "Sin señal particular": "No particular signal",
    "Recurrente en el mismo punto": "Recurring at the same spot",
    "Alta intensidad": "High intensity",
    "Sin dato": "No data",
}


def senal_txt(x):
    if st.session_state.get("idioma", "en") == "en":
        return SENALES_EN.get(str(x), str(x))
    return str(x)


MOTIVOS_EN = {
    "Manejo de pastizal o pastura": "Grassland or pasture management",
    "Limpieza de rastrojo agrícola": "Agricultural stubble clearing",
    "Cortafuego / prevención": "Firebreak / prevention",
    "Manejo de residuos vegetales": "Plant waste management",
    "Quema prescripta (manejo del fuego)": "Prescribed burn (fire management)",
    "Otro": "Other",
}


def motivo_txt(m):
    if st.session_state.get("idioma", "en") == "en":
        return MOTIVOS_EN.get(m, m)
    return m


TEXTOS["es"].update({
    "ia_titulo": "Asistente de Igneus",
    "ia_caption": "Preguntá en lenguaje simple. El asistente responde solo con los datos de la app (serie armonizada, meses críticos, anomalías y actividad reciente). Usa los filtros de provincia y fechas de la barra lateral. No es una alerta oficial: ante un incendio, llamá al 100 o al 911.",
    "ia_sin_ia": "Modo sin IA: falta configurar la clave del proveedor en `.streamlit/secrets.toml` (ver docs/asistente.md). Mientras tanto se muestra un resumen automático del área seleccionada.",
    "ia_informe": "Informe semanal para brigadas",
    "ia_placeholder": "Ej.: ¿Cuándo es más peligroso el fuego en Córdoba?",
    "ia_spinner": "Consultando los datos...",
    "ia_cod": " Código {c}: {d}",
    "ia_error": "No se pudo consultar al modelo ({tipo}).{detalle}",
    "ia_borrar": "Borrar conversación",
    "ia_modelo": "Modelo: {prov} · {modelo}. Respuestas generadas con IA: verificalas con los gráficos de la app.",
    "ia_datos": "Ver los datos que usa el asistente",
    "arm_sub": "Serie armonizada entre satélites (2000 en adelante)",
    "arm_intro": "Cada satélite nuevo cambia la cantidad de detecciones aunque la actividad real no cambie: **Aqua (2002)**, **VIIRS S-NPP (2012)**, **NOAA-20 (2018)** y **NOAA-21 (2023)**. Sumarlos genera saltos falsos. Acá todo se lleva a una escala común: **equivalente VIIRS S-NPP**.",
    "arm_cap": "Usa los filtros de provincia y fechas. No usa los filtros de sensor ni de duplicados: la armonización necesita cada satélite por separado.",
    "arm_sin": "No hay datos armonizados para esos filtros.",
    "arm_umbral": "Umbral de anomalía (desvíos sobre lo normal del mes)",
    "col_mes": "mes",
    "col_det": "detecciones",
    "col_normal": "normal del mes",
    "col_desvios": "desvíos",
    "col_fuente": "fuente",
    "col_prom": "promedio del mes",
    "col_senal": "señal",
    "arm_valid_sub": "¿Funciona? Validación con años que el método no vio",
    "arm_valid_txt": "Se calculan los factores solo con 2012-{corte} y se estima VIIRS S-NPP de {corte1} en adelante a partir de MODIS Aqua. Después se compara con lo que S-NPP observó de verdad. El error es la mediana del error relativo.",
    "arm_err_mes": "Error mensual país",
    "arm_err_anual": "Error anual por provincia",
    "arm_fac_exp": "Factores de conversión VIIRS S-NPP / MODIS Aqua por provincia y mes",
    "arm_fac_cap": "Promedio nacional: {nac}. Celdas vacías: menos de {min} detecciones de Aqua en ese mes; se usa el factor anual de la provincia.",
    "arm_como": "Cómo se arma la serie: desde 2012 se usa lo observado por VIIRS S-NPP (si en un mes S-NPP no tiene datos, se estima desde NOAA-20 o NOAA-21). Entre 2002 y 2011 se estima desde MODIS Aqua, que pasa a la misma hora que S-NPP (~13:30), con un factor por provincia y mes calculado en 2012-2025. En 2000-2001 solo hay MODIS Terra: se lleva a Aqua y después a S-NPP (más incertidumbre). Los años sin datos de ningún satélite (2005 y 2010) quedan vacíos. El año en curso usa datos de casi tiempo real y puede estar incompleto. Cada valor es un conteo de detecciones térmicas, no de incendios confirmados.",
    "graf_comp": "Comparación de sensores",
    "graf_info": "Los sensores no son directamente comparables en cantidad: VIIRS tiene mayor resolución y detecta focos más pequeños que MODIS. VIIRS cubre desde 2012 y MODIS desde 2000. Faltan los datos anuales de MODIS de 2005, 2010 y 2016 (un cero en esos años es ausencia de dato, no ausencia de actividad). Cada conteo es de detecciones térmicas, no de incendios confirmados.",
    "graf_frp_sub": "Intensidad térmica acumulada",
    "graf_frp_cap": "Suma de la potencia radiativa (FRP, en MW) de las detecciones de cada mes. Es un indicador de intensidad térmica; NO mide gases ni emisiones de carbono.",
    "graf_atip_sub": "Meses atípicos",
    "graf_umbral": "Umbral (desvíos sobre el promedio del mes)",
    "graf_atip_cap": "Compara cada mes con el mismo mes de los demás años. Dejá un solo sensor para una lectura consistente.",
    "enso_sub": "El Niño / La Niña y actividad térmica",
    "enso_falta": "Falta el archivo data/oni.txt (índice ONI de NOAA).",
    "enso_rezago": "Retraso entre el clima y la actividad (meses)",
    "enso_help": "El efecto de El Niño / La Niña puede tardar meses en notarse.",
    "enso_tip": "Tip: para una serie consistente desde 2000, dejá solo MODIS en el filtro de sensor; VIIRS empieza en 2012 y cambia el nivel de los conteos. Probá también una región distinta: el efecto no es igual en todo el país.",
    "enso_info": "Esto muestra asociación, no causa. El ONI mide la temperatura del Pacífico ecuatorial. La actividad térmica también depende de quemas agrícolas, uso del suelo, sequías locales y otros factores. No se aplicó ningún test estadístico. Cada conteo es de detecciones térmicas, no de incendios confirmados.",
    "cerca_sub": "Detecciones cerca de un punto",
    "cerca_cap": "Usa los filtros de la barra lateral. Es información de detecciones satelitales, no un pronóstico ni una alerta oficial.",
    "cerca_lugar": "Lugar",
    "otro_coord": "Otro (coordenadas)",
    "lat": "Latitud",
    "lon": "Longitud",
    "radio": "Radio (km)",
    "ventana": "Ventana reciente (días)",
    "cerca_info": "Los datos cargados llegan hasta el {fin}. 'Reciente' se mide hasta esa fecha; los últimos días reales requieren el módulo de actualización.",
    "m_rec": "Detecciones recientes",
    "m_quema": "Dentro de una quema declarada",
    "m_hist": "Históricas en la zona",
    "cerca_warn": "Hay {n} detecciones térmicas dentro de {radio} km en la ventana elegida. Es una señal para observar: no confirma incendios.",
    "cerca_ok": "Sin detecciones en ese radio y ventana.",
    "or_sub": "Señales sobre el posible origen (inferidas)",
    "or_warn": "Son señales calculadas con reglas simples. NO indican la causa real (accidental, natural o controlada) ni confirman incendios.",
    "or_falta": "Falta correr agregar_senales.py y subir el parquet actualizado.",
    "or_reglas": "Reglas (en orden de prioridad): 1) Recurrente: detecciones en el mismo punto (~1 km) en 10 o más años distintos. 2) Alta intensidad: FRP en el 5% más alto de su sensor. 3) Temporada de quemas: el resto de las detecciones de julio a octubre. 4) Sin señal particular. Las reglas son provisorias.",
    "q_sub": "Quemas controladas",
    "q_warn": "Este registro reúne **declaraciones** de quemas controladas. NO es un permiso, no reemplaza la autorización de la autoridad competente y las declaraciones no están verificadas.",
    "f_nombre": "Nombre y apellido *",
    "f_rango": "Rango / cargo *",
    "f_org": "Organización *",
    "f_permiso": "N° de permiso o expediente (si tiene)",
    "f_motivo": "Motivo *",
    "f_detalle": "Detalle del motivo (opcional)",
    "f_prov": "Provincia *",
    "f_lugar": "Lugar (paraje, campo, referencia) *",
    "f_ubic": "Ubicación",
    "f_lat": "Latitud (si elegiste coordenadas)",
    "f_inicio": "Inicio",
    "f_fin": "Fin",
    "f_radio": "Radio aprox. (km)",
    "f_acepto": "Declaro que la información es verdadera y que cuento con la autorización correspondiente.",
    "f_enviar": "Registrar declaración",
    "o_nombre": "nombre",
    "o_rango": "rango",
    "o_org": "organización",
    "o_lugar": "lugar",
    "q_complete": "Completá: {campos}",
    "q_fin": "La fecha de fin no puede ser anterior al inicio.",
    "q_14": "Una declaración puede cubrir hasta 14 días.",
    "q_acepto": "Tenés que aceptar la declaración.",
    "q_ok": "Declaración registrada. Aparece abajo y en la pestaña 'Cerca de mí'.",
    "q_vacio": "Todavía no hay quemas declaradas.",
    "q_cap": "El nombre, el rango y el permiso se guardan para trazabilidad y no se muestran. 'detecciones_en_zona' cuenta detecciones satelitales en ese radio y fechas.",
    "q_admin": "Administración (solo equipo)",
    "q_clave": "Clave",
    "q_desc": "Descargar registro completo",
    "q_no_decl": "Todavía no hay declaraciones.",
    "m_sub": "Método, fuentes y límites",
    "m_md": """**Datos cargados:** {n} detecciones térmicas del {f0} al {f1}. Sensores: {sensores} (satélites: {sats}).

**Fuentes**
- Detecciones térmicas: NASA FIRMS (MODIS y VIIRS), solo clase vegetación.
- Límites provinciales: API Georef del gobierno argentino.
- Fases El Niño / La Niña: Oceanic Niño Index de NOAA (CPC).

**Procesamiento**
1. Recorte a Argentina y asignación de provincia y región por ubicación.
2. Confianza unificada en baja / nominal / alta (MODIS 0-100 y VIIRS l/n/h).
3. Duplicados entre sensores: una cuadrícula de 0,01° (~1 km) por día; se conserva la detección de mayor confianza y FRP. Puede unir también detecciones del mismo sensor y no une las que caen en celdas vecinas.
4. Armonización de la serie entre satélites (pestaña Armonización): todo se lleva a "equivalente VIIRS S-NPP". Desde 2012 se usa S-NPP observado; antes se estima desde MODIS Aqua (y Terra en 2000-2001) con factores por provincia y mes ajustados en los años en que los satélites se superponen, y validados con años que el método no usó.
5. Los datos más recientes provienen de productos de casi tiempo real (NRT), que pueden cambiar cuando se publique la versión estándar.

**Límites que hay que tener presentes**
- Un foco de calor NO es un incendio confirmado: puede ser una quema agrícola, una fuente industrial u otra anomalía térmica.
- MODIS y VIIRS no son comparables en cantidad: VIIRS tiene mayor resolución.
- Las "señales de origen" son reglas simples, no la causa real.
- Los años o meses sin datos de algún sensor no significan ausencia de actividad.
- Las quemas declaradas dependen de que se carguen avisos oficiales con fuente.
""",
    "m_cap": "Texto científico a cargo de Luis; documentación de decisiones a cargo de A4.",
    "gases_info": "Próximamente: emisiones de carbono por incendios (CAMS GFAS). Datos en preparación.",
    "d_cap": "Se muestran las primeras 5.000 filas.",
    "d_btn": "Preparar descarga (hasta 200.000 filas más recientes)",
    "d_dl": "Descargar CSV",
})

TEXTOS["en"].update({
    "ia_titulo": "Igneus Assistant",
    "ia_caption": "Ask in plain language. The assistant answers only with the app's data (harmonized series, critical months, anomalies and recent activity). It uses the province and date filters in the sidebar. It is not an official alert: in case of a fire, call 100 or 911.",
    "ia_sin_ia": "No-AI mode: the provider key is not configured in `.streamlit/secrets.toml` (see docs/asistente.md). Meanwhile, an automatic summary of the selected area is shown.",
    "ia_informe": "Weekly report for brigades",
    "ia_placeholder": "E.g.: When is fire most dangerous in Córdoba?",
    "ia_spinner": "Querying the data...",
    "ia_cod": " Code {c}: {d}",
    "ia_error": "Could not query the model ({tipo}).{detalle}",
    "ia_borrar": "Clear conversation",
    "ia_modelo": "Model: {prov} · {modelo}. AI-generated answers: check them against the app's charts.",
    "ia_datos": "View the data the assistant uses",
    "arm_sub": "Harmonized series across satellites (2000 onward)",
    "arm_intro": "Each new satellite changes the number of detections even if real activity does not: **Aqua (2002)**, **VIIRS S-NPP (2012)**, **NOAA-20 (2018)** and **NOAA-21 (2023)**. Adding them up creates false jumps. Here everything is brought to a common scale: **VIIRS S-NPP equivalent**.",
    "arm_cap": "Uses the province and date filters. It does not use the sensor or duplicate filters: harmonization needs each satellite separately.",
    "arm_sin": "No harmonized data for these filters.",
    "arm_umbral": "Anomaly threshold (standard deviations above the month's normal)",
    "col_mes": "month",
    "col_det": "detections",
    "col_normal": "monthly normal",
    "col_desvios": "deviations",
    "col_fuente": "source",
    "col_prom": "monthly average",
    "col_senal": "signal",
    "arm_valid_sub": "Does it work? Validation with years the method did not see",
    "arm_valid_txt": "The factors are computed only with 2012-{corte}, and VIIRS S-NPP is estimated from {corte1} onward using MODIS Aqua. The estimate is then compared with what S-NPP actually observed. The error is the median relative error.",
    "arm_err_mes": "Monthly error, country",
    "arm_err_anual": "Annual error by province",
    "arm_fac_exp": "VIIRS S-NPP / MODIS Aqua conversion factors by province and month",
    "arm_fac_cap": "National average: {nac}. Empty cells: fewer than {min} Aqua detections in that month; the province's annual factor is used.",
    "arm_como": "How the series is built: from 2012 the observed VIIRS S-NPP data is used (if S-NPP has no data in a month, it is estimated from NOAA-20 or NOAA-21). Between 2002 and 2011 it is estimated from MODIS Aqua, which passes at the same time as S-NPP (~13:30), with a factor by province and month computed in 2012-2025. In 2000-2001 only MODIS Terra exists: it is brought to Aqua and then to S-NPP (more uncertainty). Years with no data from any satellite (2005 and 2010) remain empty. The current year uses near-real-time data and may be incomplete. Each value is a count of thermal detections, not of confirmed wildfires.",
    "graf_comp": "Sensor comparison",
    "graf_info": "The sensors are not directly comparable in quantity: VIIRS has higher resolution and detects smaller hotspots than MODIS. VIIRS covers 2012 onward and MODIS 2000 onward. MODIS annual data for 2005, 2010 and 2016 are missing (a zero in those years means absence of data, not absence of activity). Each count is of thermal detections, not of confirmed wildfires.",
    "graf_frp_sub": "Cumulative thermal intensity",
    "graf_frp_cap": "Sum of the fire radiative power (FRP, in MW) of each month's detections. It is a thermal intensity indicator; it does NOT measure gases or carbon emissions.",
    "graf_atip_sub": "Unusual months",
    "graf_umbral": "Threshold (standard deviations above the month's average)",
    "graf_atip_cap": "Compares each month with the same month in other years. Keep a single sensor for a consistent reading.",
    "enso_sub": "El Niño / La Niña and thermal activity",
    "enso_falta": "Missing file data/oni.txt (NOAA ONI index).",
    "enso_rezago": "Lag between climate and activity (months)",
    "enso_help": "The effect of El Niño / La Niña can take months to show up.",
    "enso_tip": "Tip: for a consistent series since 2000, keep only MODIS in the sensor filter; VIIRS starts in 2012 and changes the level of the counts. Also try a different region: the effect is not the same across the whole country.",
    "enso_info": "This shows association, not causation. The ONI measures the temperature of the equatorial Pacific. Thermal activity also depends on agricultural burning, land use, local droughts and other factors. No statistical test was applied. Each count is of thermal detections, not of confirmed wildfires.",
    "cerca_sub": "Detections near a point",
    "cerca_cap": "Uses the sidebar filters. This is satellite detection information, not a forecast or an official alert.",
    "cerca_lugar": "Place",
    "otro_coord": "Other (coordinates)",
    "lat": "Latitude",
    "lon": "Longitude",
    "radio": "Radius (km)",
    "ventana": "Recent window (days)",
    "cerca_info": "The loaded data runs up to {fin}. 'Recent' is measured up to that date; the latest real days require the update module.",
    "m_rec": "Recent detections",
    "m_quema": "Inside a declared burn",
    "m_hist": "Historical in the area",
    "cerca_warn": "There are {n} thermal detections within {radio} km in the chosen window. It is a signal to watch: it does not confirm wildfires.",
    "cerca_ok": "No detections in that radius and window.",
    "or_sub": "Signals about the possible origin (inferred)",
    "or_warn": "These are signals computed with simple rules. They do NOT indicate the real cause (accidental, natural or controlled) nor confirm wildfires.",
    "or_falta": "agregar_senales.py needs to be run and the updated parquet uploaded.",
    "or_reglas": "Rules (in priority order): 1) Recurring: detections at the same point (~1 km) in 10 or more different years. 2) High intensity: FRP in the top 5% of its sensor. 3) Burning season: the rest of the detections from July to October. 4) No particular signal. The rules are provisional.",
    "q_sub": "Controlled burns",
    "q_warn": "This record gathers **declarations** of controlled burns. It is NOT a permit, does not replace authorization from the competent authority, and the declarations are not verified.",
    "f_nombre": "Full name *",
    "f_rango": "Rank / position *",
    "f_org": "Organization *",
    "f_permiso": "Permit or file number (if any)",
    "f_motivo": "Reason *",
    "f_detalle": "Reason details (optional)",
    "f_prov": "Province *",
    "f_lugar": "Place (locality, field, landmark) *",
    "f_ubic": "Location",
    "f_lat": "Latitude (if you chose coordinates)",
    "f_inicio": "Start",
    "f_fin": "End",
    "f_radio": "Approx. radius (km)",
    "f_acepto": "I declare that the information is true and that I have the corresponding authorization.",
    "f_enviar": "Submit declaration",
    "o_nombre": "name",
    "o_rango": "rank",
    "o_org": "organization",
    "o_lugar": "place",
    "q_complete": "Please fill in: {campos}",
    "q_fin": "The end date cannot be before the start date.",
    "q_14": "A declaration can cover up to 14 days.",
    "q_acepto": "You must accept the declaration.",
    "q_ok": "Declaration registered. It appears below and in the 'Near me' tab.",
    "q_vacio": "There are no declared burns yet.",
    "q_cap": "Name, rank and permit are stored for traceability and are not displayed. 'detections_in_area' counts satellite detections within that radius and dates.",
    "q_admin": "Administration (team only)",
    "q_clave": "Password",
    "q_desc": "Download full record",
    "q_no_decl": "There are no declarations yet.",
    "m_sub": "Method, sources and limits",
    "m_md": """**Loaded data:** {n} thermal detections from {f0} to {f1}. Sensors: {sensores} (satellites: {sats}).

**Sources**
- Thermal detections: NASA FIRMS (MODIS and VIIRS), vegetation class only.
- Provincial boundaries: Argentine government Georef API.
- El Niño / La Niña phases: NOAA (CPC) Oceanic Niño Index.

**Processing**
1. Clipping to Argentina and assignment of province and region by location.
2. Confidence unified into low / nominal / high (MODIS 0-100 and VIIRS l/n/h).
3. Duplicates between sensors: a 0.01° (~1 km) grid per day; the detection with the highest confidence and FRP is kept. It may also merge detections from the same sensor and does not merge those falling in neighboring cells.
4. Harmonization of the series across satellites (Harmonization tab): everything is brought to "VIIRS S-NPP equivalent". From 2012 observed S-NPP is used; before that it is estimated from MODIS Aqua (and Terra in 2000-2001) with factors by province and month fitted in the years when the satellites overlap, and validated with years the method did not use.
5. The most recent data come from near-real-time (NRT) products, which may change when the standard version is published.

**Limits to keep in mind**
- A heat hotspot is NOT a confirmed wildfire: it may be an agricultural burn, an industrial source or another thermal anomaly.
- MODIS and VIIRS are not comparable in quantity: VIIRS has higher resolution.
- The "origin signals" are simple rules, not the real cause.
- Years or months without data from a sensor do not mean absence of activity.
- Declared burns depend on official notices being loaded with a source.
""",
    "m_cap": "Scientific text by Luis; decision documentation by A4.",
    "gases_info": "Coming soon: carbon emissions from wildfires (CAMS GFAS). Data in preparation.",
    "d_cap": "Showing the first 5,000 rows.",
    "d_btn": "Prepare download (up to the 200,000 most recent rows)",
    "d_dl": "Download CSV",
})

TEXTOS["es"].update({
    "g_mes": "Mes", "g_det": "Detecciones", "g_det_lc": "detecciones",
    "g_sensor": "Sensor", "g_anio": "Año", "g_fecha": "Fecha",
    "g_pct_det": "% de detecciones", "g_confianza": "Confianza",
    "g_provincia": "Provincia", "g_fase": "Fase", "g_act_rel": "Actividad relativa",
    "g_t_mensual": "Detecciones térmicas por mes y sensor",
    "g_t_cal": "Calendario de detecciones térmicas {anio}",
    "g_t_anio_mes": "Actividad térmica por año y mes",
    "g_t_comp": "Detecciones por año y sensor",
    "g_t_estac": "Estacionalidad: detecciones por mes del año",
    "g_t_conf": "Distribución de confianza por sensor (%)",
    "g_t_prov": "Detecciones térmicas por provincia",
    "g_t_enso_m": "Detecciones mensuales y fases de El Niño / La Niña",
    "g_t_enso_f": "Actividad relativa según la fase (1 = típico para ese mes)",
    "g_conf_baja": "baja", "g_conf_nominal": "nominal", "g_conf_alta": "alta",
    "g_conf_desconocida": "desconocida",
    "g_f_nino": "El Niño", "g_f_nina": "La Niña", "g_f_neutro": "Neutro",
    "g_etq_fase": "{fase} (n={n} meses)",
})

TEXTOS["en"].update({
    "g_mes": "Month", "g_det": "Detections", "g_det_lc": "detections",
    "g_sensor": "Sensor", "g_anio": "Year", "g_fecha": "Date",
    "g_pct_det": "% of detections", "g_confianza": "Confidence",
    "g_provincia": "Province", "g_fase": "Phase", "g_act_rel": "Relative activity",
    "g_t_mensual": "Thermal detections per month and sensor",
    "g_t_cal": "Thermal detections calendar {anio}",
    "g_t_anio_mes": "Thermal activity by year and month",
    "g_t_comp": "Detections per year and sensor",
    "g_t_estac": "Seasonality: detections by month of the year",
    "g_t_conf": "Confidence distribution by sensor (%)",
    "g_t_prov": "Thermal detections by province",
    "g_t_enso_m": "Monthly detections and El Niño / La Niña phases",
    "g_t_enso_f": "Relative activity by phase (1 = typical for that month)",
    "g_conf_baja": "low", "g_conf_nominal": "nominal", "g_conf_alta": "high",
    "g_conf_desconocida": "unknown",
    "g_f_nino": "El Niño", "g_f_nina": "La Niña", "g_f_neutro": "Neutral",
    "g_etq_fase": "{fase} (n={n} months)",
})

TEXTOS["es"].update({
    "x_radio": "Radio {radio} km", "x_tupunto": "Tu punto", "x_quema": "Quema declarada",
    "x_dist": "Distancia (km)",
    "x_t_estac_zona": "Meses con actividad en esta zona (todos los años)",
    "x_t_anual_zona": "Detecciones por año en esta zona",
    "x_t_senales": "Señales por año (% de detecciones)", "x_senal": "Señal",
    "x_anom_alto": "Muy por encima del promedio", "x_anom_norm": "Dentro de lo habitual",
    "x_anom_prom": "Promedio histórico del mes",
    "x_t_anom": "Meses con actividad térmica muy por encima de lo habitual",
    "x_t_frp": "Intensidad térmica acumulada por mes (suma de FRP)",
    "x_frp": "Suma de FRP (MW)",
    "x_t_dens": "Detecciones cada 1.000 km² (comparable entre provincias)",
    "x_dens": "Detecciones por 1.000 km²", "x_n": "Detecciones", "x_km2": "Superficie (km²)",
    "x_estado_decl": "Declarada (sin verificar)",
    "rq_provincia": "provincia", "rq_lugar": "lugar", "rq_organizacion": "organización",
    "rq_motivo": "motivo", "rq_desde": "desde", "rq_hasta": "hasta",
    "rq_radio": "radio_km", "rq_estado": "estado", "rq_det": "detecciones_en_zona",
})

TEXTOS["en"].update({
    "x_radio": "Radius {radio} km", "x_tupunto": "Your point", "x_quema": "Declared burn",
    "x_dist": "Distance (km)",
    "x_t_estac_zona": "Months with activity in this area (all years)",
    "x_t_anual_zona": "Detections per year in this area",
    "x_t_senales": "Signals per year (% of detections)", "x_senal": "Signal",
    "x_anom_alto": "Well above average", "x_anom_norm": "Within the usual range",
    "x_anom_prom": "Historical average for the month",
    "x_t_anom": "Months with thermal activity well above the usual",
    "x_t_frp": "Cumulative thermal intensity per month (sum of FRP)",
    "x_frp": "Sum of FRP (MW)",
    "x_t_dens": "Detections per 1,000 km² (comparable across provinces)",
    "x_dens": "Detections per 1,000 km²", "x_n": "Detections", "x_km2": "Area (km²)",
    "x_estado_decl": "Declared (unverified)",
    "rq_provincia": "province", "rq_lugar": "place", "rq_organizacion": "organization",
    "rq_motivo": "reason", "rq_desde": "from", "rq_hasta": "to",
    "rq_radio": "radius_km", "rq_estado": "status", "rq_det": "detections_in_area",
})

MESES_ABREV_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_ABREV_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def meses_abrev():
    return MESES_ABREV_EN if t("h_lang") == "en" else MESES_ABREV_ES


METODOS_EN = {
    "Observado (VIIRS S-NPP)": "Observed (VIIRS S-NPP)",
    "Estimado desde VIIRS NOAA-20": "Estimated from VIIRS NOAA-20",
    "Estimado desde VIIRS NOAA-21": "Estimated from VIIRS NOAA-21",
    "Estimado desde MODIS Aqua": "Estimated from MODIS Aqua",
    "Estimado desde MODIS Terra": "Estimated from MODIS Terra",
    "Sin datos": "No data",
}

VALID_EN = {
    "Factor por provincia y mes (el nuestro)": "Factor by province and month (ours)",
    "Factor único nacional": "Single national factor",
    "Sumar todos los satélites (sin armonizar)": "Sum of all satellites (not harmonized)",
}


def metodo_txt(x):
    return METODOS_EN.get(x, x) if t("h_lang") == "en" else x


def valid_txt(x):
    return VALID_EN.get(x, x) if t("h_lang") == "en" else x


TEXTOS["es"].update({
    "h_lang": "es",
    "h_suma_cruda": "Suma cruda de todos los satélites",
    "h_serie_arm": "Serie armonizada (equivalente VIIRS S-NPP)",
    "h_en_curso": "año en curso<br>(incompleto)",
    "h_ad_title": "Antes y después: sumar satélites vs. serie armonizada",
    "h_anio": "Año",
    "h_mes": "Mes",
    "h_det_anio": "Detecciones por año",
    "h_det_eq": "Detecciones (eq. S-NPP)",
    "h_cal_title": "Calendario armonizado de actividad de quema",
    "h_critico": "Período crítico",
    "h_resto": "Resto del año",
    "h_prom_arm": "Promedio armonizado",
    "h_crit_title": "Períodos críticos: actividad promedio de cada mes (armonizada)",
    "h_armonizado": "Armonizado",
    "h_normal_mes": "Normal para ese mes",
    "h_atipico": "Atípico (≥ {umbral} desvíos)",
    "h_anom_title": "Condiciones fuera de lo normal (sobre la serie armonizada)",
    "h_det_mes_eq": "Detecciones por mes (eq. S-NPP)",
    "h_obs": "VIIRS S-NPP observado",
    "h_est_local": "Estimado: factor por provincia y mes",
    "h_est_unico": "Estimado: factor único nacional",
    "h_val_title": "Validación: años {corte1} en adelante, que el método no usó para ajustarse",
    "h_det_mes": "Detecciones por mes",
    "h_todo_anio": "Todo el año",
    "h_col_metodo": "Método",
})

TEXTOS["en"].update({
    "h_lang": "en",
    "h_suma_cruda": "Raw sum of all satellites",
    "h_serie_arm": "Harmonized series (VIIRS S-NPP equivalent)",
    "h_en_curso": "current year<br>(incomplete)",
    "h_ad_title": "Before and after: summing satellites vs. harmonized series",
    "h_anio": "Year",
    "h_mes": "Month",
    "h_det_anio": "Detections per year",
    "h_det_eq": "Detections (S-NPP eq.)",
    "h_cal_title": "Harmonized burning activity calendar",
    "h_critico": "Critical period",
    "h_resto": "Rest of the year",
    "h_prom_arm": "Harmonized average",
    "h_crit_title": "Critical periods: average activity of each month (harmonized)",
    "h_armonizado": "Harmonized",
    "h_normal_mes": "Normal for that month",
    "h_atipico": "Unusual (≥ {umbral} deviations)",
    "h_anom_title": "Out-of-the-ordinary conditions (on the harmonized series)",
    "h_det_mes_eq": "Detections per month (S-NPP eq.)",
    "h_obs": "VIIRS S-NPP observed",
    "h_est_local": "Estimated: factor by province and month",
    "h_est_unico": "Estimated: single national factor",
    "h_val_title": "Validation: years {corte1} onward, which the method did not use for fitting",
    "h_det_mes": "Detections per month",
    "h_todo_anio": "Whole year",
    "h_col_metodo": "Method",
})

TEXTOS["es"].update({
    "cm_titulo": "Cómo se usa esta sección",
    "cm_md": """**Qué es.** Los satélites de la NASA detectan puntos de la superficie con una temperatura anormalmente alta. Se llaman *focos de calor*. Esta sección te muestra cuántos hubo cerca de un lugar que elijas. Un foco de calor **no es un incendio confirmado**: puede ser una quema agrícola, una fuente industrial u otra cosa.

**Cómo usarla, paso a paso**
1. **Lugar:** elegí uno de la lista. Si el tuyo no está, elegí "Otro (coordenadas)" y escribí la latitud y la longitud. Podés copiarlas desde Google Maps: tocá y mantené sobre el punto y aparecen los números.
2. **Radio:** es la distancia alrededor del lugar que querés revisar, en kilómetros. Con 20 km se empieza bien.
3. **Ventana reciente:** cuántos días hacia atrás querés mirar. Por defecto son 30.
4. Mirá el resultado: los tres números, el mapa y el mensaje de color.

**Cómo leer el resultado**
- **Detecciones recientes:** focos dentro del radio y de los días que elegiste.
- **Dentro de una quema declarada:** de esos focos, cuántos caen en una quema controlada que alguien registró en la pestaña Quemas. Si hay coincidencia, es probable que el foco sea esa quema.
- **Históricas en la zona:** cuántos focos hubo en esa zona entre 2000 y 2026. Sirve para comparar: si hay pocos recientes pero muchos históricos, la zona suele tener actividad.
- **Mapa:** cada punto es un foco dentro del radio.
- **Mensaje de color:** te avisa si hay detecciones o si no hay ninguna.
- **Gráficos de abajo:** muestran en qué época del año y en qué años hubo más focos en esa zona.

**Un ejemplo.** Querés saber si hubo focos cerca de tu campo en la última semana: elegí tu ubicación, poné un radio de 10 km y una ventana de 7 días.

**Para tener en cuenta.** "Reciente" se cuenta hasta el último día con datos cargados (figura arriba, en "último dato"), no hasta hoy. Los filtros de la barra lateral (fechas, provincias, sensores) también se aplican acá. Esta sección informa detecciones satelitales: no es un pronóstico ni una alerta oficial. Ante un incendio, llamá al 100 o al 911.""",
})

TEXTOS["en"].update({
    "cm_titulo": "How to use this section",
    "cm_md": """**What it is.** NASA satellites detect spots on the surface with an unusually high temperature. They are called *heat hotspots*. This section shows how many there were near a place you choose. A heat hotspot is **not a confirmed wildfire**: it may be an agricultural burn, an industrial source or something else.

**How to use it, step by step**
1. **Place:** pick one from the list. If yours is not there, choose "Other (coordinates)" and type the latitude and longitude. You can copy them from Google Maps: press and hold on the spot and the numbers appear.
2. **Radius:** the distance around the place that you want to check, in kilometers. 20 km is a good start.
3. **Recent window:** how many days back you want to look. The default is 30.
4. Read the result: the three numbers, the map and the colored message.

**How to read the result**
- **Recent detections:** hotspots within the radius and the days you chose.
- **Inside a declared burn:** of those hotspots, how many fall inside a controlled burn that someone registered in the Controlled burns tab. If there is a match, the hotspot is probably that burn.
- **Historical in the area:** how many hotspots there were in that area between 2000 and 2026. Useful for comparison: few recent ones but many historical ones means the area is usually active.
- **Map:** each point is a hotspot within the radius.
- **Colored message:** tells you whether there are detections or none.
- **Charts below:** show in which time of year and in which years there were more hotspots in that area.

**An example.** You want to know whether there were hotspots near your farm in the last week: choose your location, set a radius of 10 km and a window of 7 days.

**Keep in mind.** "Recent" is counted up to the last day with loaded data (shown at the top, under "latest data"), not up to today. The sidebar filters (dates, provinces, sensors) also apply here. This section reports satellite detections: it is not a forecast or an official alert. In case of a fire, call 100 or 911.""",
})