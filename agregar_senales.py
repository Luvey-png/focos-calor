from pathlib import Path
import numpy as np
import pandas as pd

PARQUET = Path("data/focos_real.parquet")

# Reglas provisorias: las define Luis y las anota A4
UMBRAL_ANIOS = 10             # mismo punto (~1 km) con detecciones en >= 10 años distintos
PERCENTIL_INTENSIDAD = 0.95   # FRP en el 5% más alto de su sensor
MESES_TEMPORADA = (7, 8, 9, 10)


def main():
    df = pd.read_parquet(PARQUET).drop(columns=["senal"], errors="ignore")
    anio = df["fecha"].dt.year
    mes = df["fecha"].dt.month

    # celda de ~1 km (0,01°) como número entero
    celda = (
        ((df["latitud"].astype("float64") * 100).round().astype("int64") + 6000) * 20000
        + ((df["longitud"].astype("float64") * 100).round().astype("int64") + 8000)
    )
    par = pd.DataFrame({"celda": celda, "anio": anio}).drop_duplicates()
    n_anios = par.groupby("celda").size()
    anios_celda = celda.map(n_anios)

    sensor = df["sensor"].astype(str)
    p = df.groupby(sensor)["frp"].quantile(PERCENTIL_INTENSIDAD)
    alta = df["frp"] >= sensor.map(p)

    df["senal"] = np.select(
        [anios_celda >= UMBRAL_ANIOS, alta, mes.isin(MESES_TEMPORADA)],
        ["Recurrente en el mismo punto", "Alta intensidad",
         "Temporada habitual de quemas (jul-oct)"],
        default="Sin señal particular",
    )
    df["senal"] = df["senal"].astype("category")
    df.to_parquet(PARQUET, index=False)

    print(df["senal"].value_counts())
    print(f"Tamaño: {PARQUET.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()