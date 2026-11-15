# Armonización de la serie entre satélites

**Rama:** `armonizacion-sensores`\
**Archivos:** `armonizacion.py` (nuevo), `app.py`, `extras.py`\
**Fecha:** 15/11/2026

## 1. El problema

El desafío pide armonizar los registros de focos de calor de MODIS y VIIRS en un
calendario de actividad de quema. En los datos de FIRMS, cada vez que se suma un
satélite nuevo cambia la cantidad de detecciones, aunque la actividad real no
cambie:

| Año  | Entra                    | Efecto en los conteos                        |
|------|--------------------------|----------------------------------------------|
| 2000 | MODIS Terra              | Inicio de la serie (desde noviembre)         |
| 2002 | MODIS Aqua               | Casi duplica los conteos de MODIS            |
| 2012 | VIIRS S-NPP (375 m)      | ~5 veces más detecciones que MODIS Aqua      |
| 2018 | VIIRS NOAA-20            | Duplica los conteos de VIIRS                 |
| 2023 | VIIRS NOAA-21            | Vuelve a sumar detecciones de VIIRS          |

Antes de este cambio, la opción "Armonizado" de la app solo quitaba duplicados
(misma celda de ~1 km y mismo día). Eso no corrige la diferencia de escala entre
satélites: la serie anual seguía saltando de ~70.000 detecciones en 2011 a
~146.000 en 2012.

## 2. El método

Toda la serie se lleva a una escala común: **equivalente VIIRS S-NPP**.

1. **2012 en adelante:** se usa lo observado por VIIRS S-NPP. Es un solo satélite,
   así que la serie es consistente y no le afectan NOAA-20 ni NOAA-21.
   Si en un mes S-NPP no tiene datos suficientes (pasa en los datos recientes de
   2026), se estima desde **VIIRS NOAA-20** y, si tampoco hay, desde **NOAA-21**,
   con un factor S-NPP/NOAA por provincia y mes calculado en los meses en que
   coinciden. El factor de NOAA-21 tiene más incertidumbre porque solo hay pocos
   meses en común (agosto a octubre de 2026).
2. **2002–2011:** se estima S-NPP a partir de MODIS Aqua.
   `S-NPP estimado = Aqua × factor(provincia, mes)`
   - Aqua y S-NPP pasan a la misma hora (~13:30 local), así que ven el mismo ciclo
     diario del fuego.
   - El factor es `Σ S-NPP / Σ Aqua` en los años completos en que funcionan los
     dos (hoy: 2013–2015, 2017–2021, 2023 y 2025).
   - Se calcula por provincia y mes del año, porque cambia según el tipo de fuego y
     la estación (por ejemplo, San Luis: 3,4 en julio y 8,3 en diciembre).
   - Si una provincia tiene menos de 20 detecciones de Aqua en ese mes, se usa el
     factor anual de la provincia, y si no alcanza, el nacional (~5,4).
3. **2000–2001:** solo hay MODIS Terra. Se lleva a Aqua con un factor Aqua/Terra
   por provincia y mes (2002–2025) y después a S-NPP. Tiene más incertidumbre.
4. **Años sin datos de ningún satélite (2005 y 2010):** quedan vacíos. No se
   inventan valores.
5. **Año en curso:** usa datos de casi tiempo real (NRT) y puede estar incompleto.
   No se usa para calcular factores ni para validar.

Se cuentan las detecciones de cada satélite por separado (sin quitar duplicados),
agrupadas por año, mes y provincia. Un satélite se considera **disponible** en un
mes si tiene datos en al menos el 70 % de los días que cubre la base ese mes. Así,
por ejemplo, S-NPP en noviembre de 2026 (2 días de 14) no cuenta como dato y se usa
NOAA-20. Un mes sin detecciones en una provincia cuenta como cero real solo si el
satélite estaba disponible.

## 3. Validación

Para saber si el método funciona, se calculan los factores **solo con 2012–2018**
y se estima S-NPP de **2019–2025** a partir de Aqua, años que el método no vio
(se usan los años completos: 2019, 2020, 2021, 2023 y 2025).
Después se compara con lo que S-NPP observó de verdad. El error es la mediana del
error relativo.

| Método                                    | Error mensual (país) | Error anual por provincia |
|-------------------------------------------|----------------------|---------------------------|
| **Factor por provincia y mes (el nuestro)** | **7,3 %**            | **12,0 %**                |
| Factor único nacional                     | 23,2 %               | 13,8 %                    |
| Sumar todos los satélites (sin armonizar) | 126 %                | 127 %                     |

Para el error mensual se usan los meses con al menos 100 detecciones, y para el
anual por provincia, las provincias con al menos 200 detecciones en el año.

## 4. Qué se ve en la app

Hay una pestaña nueva, **"Armonización"** (después de "Calendario"):

- **Antes y después:** barras con la suma cruda de todos los satélites y una línea
  con la serie armonizada, con líneas verticales en cada lanzamiento de satélite.
- **Calendario armonizado:** mapa de calor año × mes.
- **Períodos críticos:** promedio armonizado de cada mes, con el 25 % más alto
  resaltado.
- **Condiciones fuera de lo normal:** meses que superan el umbral de desvíos
  respecto del promedio de ese mes. La tabla indica si el valor es observado o
  estimado.
- **Validación:** la tabla de errores y el gráfico de observado contra estimado.
- **Factores de conversión** por provincia y mes, en un desplegable.

La pestaña usa los filtros de **provincia y fechas**. No usa los de sensor ni de
duplicados, porque la armonización necesita cada satélite por separado.

**Otros cambios:**

- El filtro "Armonizado (sin duplicados entre sensores)" pasa a llamarse
  **"Quitar duplicados entre sensores"**, con una ayuda que apunta a la pestaña
  nueva. El comportamiento no cambia.
- En "Método y fuentes" se agrega el punto 4, que describe la armonización.
- Se elimina la primera definición duplicada de `grafico_senales` en `extras.py`.
  Antes se usaba la segunda, así que el resultado no cambia.

## 5. Estructura de `armonizacion.py`

| Función                          | Qué hace                                                                 |
|----------------------------------|--------------------------------------------------------------------------|
| `tabla_mensual(df)`              | Conteos por año, mes, provincia y satélite, con la disponibilidad de cada satélite |
| `anios_completos(m, *sats)`      | Años en que esos satélites tienen datos los 12 meses                     |
| `ajustar(m)`                     | Calcula los factores S-NPP/Aqua y Aqua/Terra                             |
| `armonizar(m, factores)`         | Agrega las columnas `armonizado`, `metodo` y `suma_cruda`                |
| `validar(m, corte=2018)`         | Ajusta hasta `corte`, valida en los años siguientes y devuelve la tabla de errores y la serie |
| `filtrar`, `anual`, `mensual_total`, `anomalias` | Resúmenes para la app                                |
| `grafico_*`, `tabla_factores`    | Gráficos y tabla de la pestaña                                           |

En `app.py`, `preparar_armonizacion(_df, version)` calcula todo una sola vez y lo
guarda en caché. Se recalcula si cambian los archivos parquet. Tarda unos 3
segundos con los ~6 millones de detecciones.

## 6. Límites

- Son conteos de **detecciones térmicas**, no de incendios confirmados.
- El factor supone que la relación S-NPP/Aqua de 2012–2025 vale también para
  2002–2011. La validación muestra que es estable en el tiempo, pero puede variar
  si cambia mucho el tipo de fuego de una zona.
- 2000–2001 se estiman desde Terra con dos factores encadenados, así que tienen más
  incertidumbre.
- La órbita de Terra se fue corriendo en los últimos años, pero no afecta porque
  Terra solo se usa en 2000–2001.
- Faltan los datos de MODIS de 2005, 2010 y 2016. En 2016 no importa porque se usa
  S-NPP.
- Se armonizan conteos, no la potencia del fuego (FRP).

## 7. Posibles mejoras

- Reemplazar el factor por un modelo de machine learning (por ejemplo,
  *gradient boosting*) que use FRP, cobertura del suelo, latitud y estación, y
  comparar su error con el de esta tabla.
- Armonizar también la FRP acumulada.
- Completar MODIS 2005 y 2010 desde el archivo de FIRMS.
- Hacer que el calendario de la pestaña "Calendario" use la serie armonizada.

## 8. Uso de IA

Este cambio se desarrolló con ayuda de un asistente de IA (Claude). La
armonización es estadística, calculada con los datos, y no usa IA dentro de la app.
Hay que mencionarlo en la declaración de uso de IA de la entrega, como pide Space
Apps.
