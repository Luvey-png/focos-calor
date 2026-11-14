import json
from pathlib import Path
import pandas as pd

CARPETA_RAW = Path("data/raw")
SALIDA = Path("data/focos_real.parquet")

# Rectángulo aproximado de Argentina continental (Luis/A1: confirmar).
# OJO: incluye partes de Chile, Uruguay, Paraguay, Bolivia y Brasil.
LAT_MIN, LAT_MAX = -55.1, -21.7
LON_MIN, LON_MAX = -73.6, -53.6


def nivel_confianza(valor):
    v = str(valor).strip().lower()
    if v in ("l", "low"):
        return "baja"
    if v in ("n", "nominal"):
        return "nominal"
    if v in ("h", "high"):
        return "alta"
    try:
        n = float(v)
    except ValueError:
        return "desconocida"
    if n < 30:
        return "baja"
    if n < 80:
        return "nominal"
    return "alta"


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    if isinstance(datos, dict):
        datos = datos.get("data", [datos])
    return pd.DataFrame(datos)


def procesar(df):
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df[
        df["latitude"].between(LAT_MIN, LAT_MAX)
        & df["longitude"].between(LON_MIN, LON_MAX)
    ]
    out = pd.DataFrame()
    out["sensor"] = df["instrument"].astype(str).str.upper().astype("category")
    out["fecha"] = pd.to_datetime(df["acq_date"])
    out["latitud"] = df["latitude"].astype("float32")
    out["longitud"] = df["longitude"].astype("float32")
    out["confianza"] = df["confidence"].apply(nivel_confianza).astype("category")
    out["confianza_original"] = df["confidence"].astype(str).astype("category")
    out["fuente"] = "FIRMS"
    out["es_prueba"] = False
    out["hora"] = df["acq_time"].astype(str).str.zfill(4)
    out["satelite"] = df["satellite"].astype("category")
    out["frp"] = pd.to_numeric(df["frp"], errors="coerce").astype("float32")
    out["diurno"] = df["daynight"].astype("category")
    return out


def main():
    archivos = sorted(CARPETA_RAW.glob("*.json"))
    if not archivos:
        print("No encontré .json en data/raw")
        return

    partes = []
    for ruta in archivos:
        df = leer_json(ruta)
        total = len(df)
        out = procesar(df)
        print(f"{ruta.name}: {total} filas -> {len(out)} en Argentina (aprox.)")
        partes.append(out)
        del df

    final = pd.concat(partes, ignore_index=True)
    final = final.drop_duplicates().sort_values("fecha")
    for c in ["sensor", "confianza", "confianza_original", "satelite", "diurno"]:
        final[c] = final[c].astype(str).astype("category")
    final.to_parquet(SALIDA, index=False)

    print(f"\nListo: {len(final)} detecciones en {SALIDA}")
    print(final["sensor"].value_counts())
    print(f"Tamaño: {SALIDA.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()