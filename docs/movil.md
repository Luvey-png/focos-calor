# Versión para celular

**Rama:** `armonizacion-sensores`\
**Archivos:** `estilo.py`\
**Fecha:** 15/11/2026

## 1. Qué cambia

La app se adapta sola cuando se abre desde un celular o una tablet. En la
computadora se ve igual que antes.

| Elemento | En celular |
|---|---|
| Encabezado | El logo ya no queda tapado por la barra superior de Streamlit |
| Indicadores (detecciones, período, etc.) | Se acomodan de a dos por fila |
| Títulos de los gráficos | Se muestran como texto arriba del gráfico y ocupan las líneas que necesiten (antes se cortaban) |
| Leyendas y barras de colores | Pasan arriba del gráfico, en horizontal, para que el gráfico use todo el ancho |
| Botones de Plotly (zoom, descarga) | Se ocultan, porque tapaban los títulos y se tocaban sin querer |
| Márgenes y letras | Más chicos |
| Botones | Ocupan todo el ancho, así son más fáciles de tocar |
| Ayuda | Un aviso explica cómo abrir los filtros y que las pestañas se deslizan hacia el costado |

Las columnas de Streamlit (por ejemplo, los indicadores de "Cerca de mí" o las
preguntas de ejemplo del asistente) se apilan solas en pantallas angostas.

## 2. Cómo funciona

Hay dos partes:

1. **CSS** (`CSS` en `estilo.py`, dentro de `@media (max-width: 640px)`):
   ajusta encabezado, títulos, avisos, botones y espacios según el ancho de la
   pantalla.
2. **Gráficos** (`es_movil()` y `ajustar_para_movil(fig)` en `estilo.py`):
   - `es_movil()` mira el navegador (*User-Agent*) para saber si es un celular o
     una tablet, y guarda el resultado en la sesión.
   - Todos los gráficos ya pasaban por `_plotly_en_espanol()`, que pone la coma
     decimal. Ahora, si es un celular, esa misma función también llama a
     `ajustar_para_movil(fig)`, saca el título del gráfico para mostrarlo como
     texto y oculta la barra de botones de Plotly.

Así, **no hace falta cambiar cada gráfico**. Cualquier gráfico nuevo que se haga
con `st.plotly_chart` se adapta solo.

## 3. Cómo probarlo

- **En un celular:** abrí la app publicada (o, en la misma red Wi-Fi, la
  dirección *Network URL* que muestra la terminal al correr `streamlit run`).
- **En la computadora:** en Chrome, `F12` → ícono de celular (*Toggle device
  toolbar*) → elegí un modelo, por ejemplo *iPhone 12 Pro*, y **recargá la
  página** (`F5`). Hay que recargar porque la detección se hace al abrir la app.

Se probó a 390 px de ancho en las pestañas Asistente IA, Mapa, Calendario,
Armonización, Gráficos, El Niño / La Niña, Cerca de mí, Origen y Quemas: no hay
desplazamiento horizontal de la página y los gráficos usan todo el ancho.

## 4. Límites

- Si se achica la ventana de una computadora, el CSS se adapta pero los gráficos
  no, porque la detección es por tipo de dispositivo y no por ancho.
- Las tablas anchas (por ejemplo, la de meses atípicos) se desplazan hacia el
  costado dentro de la tabla.
- El calendario diario (semanas × días) es denso en una pantalla chica. Se ve
  mejor con el celular en horizontal.
