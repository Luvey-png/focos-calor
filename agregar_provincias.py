import unicodedata
from pathlib import Path
import geopandas as gpd
import pandas as pd

PARQUET = Path("data/focos_real.parquet")
LIMITES = Path("data/limites/provincias.geojson")

# (clave en minúsculas sin tildes, nombre, región). CABA va primero a propósito.
PROV = [
    ("ciudad autonoma", "CABA", "Pampeana"),
    ("buenos aires", "Buenos Aires", "Pampeana"),
    ("cordoba", "Córdoba", "Pampeana"),
    ("santa fe", "Santa Fe", "Pampeana"),
    ("entre rios", "Entre Ríos", "Pampeana"),
    ("la pampa", "La Pampa", "Pampeana"),
    ("jujuy", "Jujuy", "Noroeste"),
    ("salta", "Salta", "Noroeste"),
    ("tucuman", "Tucumán", "Noroeste"),
    ("catamarca", "Catamarca", "Noroeste"),
    ("la rioja", "La Rioja", "Noroeste"),
    ("santiago del estero", "Santiago del Estero", "Noroeste"),
    ("formosa", "Formosa", "Noreste"),
    ("chaco", "Chaco", "Noreste"),
    ("corrientes", "Corrientes", "Noreste"),
    ("misiones", "Misiones", "Noreste"),
    ("mendoza", "Mendoza", "Cuyo"),
    ("san juan", "San Juan", "Cuyo"),
    ("san luis", "San Luis", "Cuyo"),
    ("neuquen", "Neuquén", "Patagonia"),
    ("rio negro", "Río Negro", "Patagonia"),
    ("chubut", "Chubut", "Patagonia"),
    ("santa cruz", "Santa Cruz", "Patagonia"),
    ("tierra del fuego", "Tierra del Fuego", "Patagonia"),
]


def sin_tildes(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def clasificar(nombre):
    n = sin_tildes(nombre)
    for clave, prov, reg in PROV:
        if clave in n:
            return prov, reg
    return None, None


def main():
    lim = gpd.read_file(LIMITES).to_crs(4326)
    col = next((c for c in ["nombre", "NAME_1", "shapeName", "name", "provincia"]
                if c in lim.columns), None)
    if col is None:
        print("No encuentro la columna de nombres. Columnas:", list(lim.columns))
        return
    res = lim[col].map(clasificar)
    lim["provincia"] = [r[0] for r in res]
    lim["region"] = [r[1] for r in res]
    sin = lim[lim["provincia"].isna()]
    if len(sin):
        print("Nombres que no pude clasificar (avisame):", sin[col].tolist())
        return
    print(f"{len(lim)} provincias cargadas")
    lim = lim[["provincia", "region", "geometry"]]

    df = pd.read_parquet(PARQUET)
    df = df.drop(columns=["provincia", "region"], errors="ignore").reset_index(drop=True)
    total = len(df)

    partes = []
    for i in range(0, total, 500_000):
        t = df.iloc[i:i + 500_000]
        pts = gpd.GeoDataFrame(
            t, geometry=gpd.points_from_xy(t["longitud"], t["latitud"]), crs=4326
        )
        j = gpd.sjoin(pts, lim, how="inner", predicate="within")
        j = j[~j.index.duplicated()]  # puntos justo en un borde
        partes.append(pd.DataFrame(j.drop(columns=["geometry", "index_right"])))
        print(f"  procesado {min(i + 500_000, total):,} / {total:,}")

    out = pd.concat(partes).sort_values("fecha")
    for c in ["sensor", "confianza", "confianza_original", "satelite",
              "diurno", "provincia", "region"]:
        out[c] = out[c].astype(str).astype("category")
        out = out.drop(columns=["hora"], errors="ignore")
    out.to_parquet(PARQUET, index=False)

    print(f"\nTotal antes: {total:,} | dentro de Argentina: {len(out):,} "
          f"| descartadas: {total - len(out):,}")
    print(out["region"].value_counts())
    print(out["provincia"].value_counts())
    print(f"Tamaño: {PARQUET.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()