import os
import sys
from datetime import date, timedelta
import geopandas as gpd
import pandas as pd
from convertir_json import nivel_confianza
from agregar_provincias import clasificar, LIMITES

BBOX = "-74,-56,-53,-21"  # oeste,sur,este,norte
PRODUCTOS = [
    ("VIIRS_SNPP_NRT", "VIIRS"), ("VIIRS_NOAA20_NRT", "VIIRS"),
    ("VIIRS_NOAA21_NRT", "VIIRS"), ("MODIS_NRT", "MODIS"),
]
VENTANA = 5  # días por consulta (verificar el máximo en la doc de la API)
SALIDA = "data/focos_recientes.parquet"


def descargar(clave, desde, hasta):
    partes, d = [], desde
    while d <= hasta:
        for prod, sensor in PRODUCTOS:
            url = (f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
                   f"{clave}/{prod}/{BBOX}/{VENTANA}/{d:%Y-%m-%d}")
            try:
                t = pd.read_csv(url)
            except Exception as e:
                print("  error", prod, d, e)
                continue
            if "latitude" not in t.columns or t.empty:
                continue
            t["sensor"] = sensor
            partes.append(t)
        print("ok", d)
        d += timedelta(days=VENTANA)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def main():
    clave = os.environ.get("FIRMS_MAP_KEY")
    if not clave:
        print("Falta la variable FIRMS_MAP_KEY (ver instrucciones).")
        return
    if len(sys.argv) > 1:
        desde = date.fromisoformat(sys.argv[1])
    else:
        ultima = pd.read_parquet("data/focos_real.parquet", columns=["fecha"])["fecha"].max()
        desde = ultima.date() + timedelta(days=1)
    t = descargar(clave, desde, date.today())
    if t.empty:
        print("No se descargó nada: revisá la clave, la fecha de inicio y los productos.")
        return
    t = t.drop_duplicates()
    if "type" in t.columns:  # solo vegetación, igual que el dataset de A1
        t = t[pd.to_numeric(t["type"], errors="coerce").fillna(0) == 0]

    out = pd.DataFrame({
        "sensor": t["sensor"].values,
        "fecha": pd.to_datetime(t["acq_date"]).values,
        "latitud": t["latitude"].astype("float32").values,
        "longitud": t["longitude"].astype("float32").values,
        "confianza": t["confidence"].map(nivel_confianza).values,
        "es_prueba": False,
        "satelite": t["satellite"].astype(str).values,
        "frp": pd.to_numeric(t["frp"], errors="coerce").astype("float32").values,
        "diurno": t["daynight"].astype(str).values,
    })

    lim = gpd.read_file(LIMITES).to_crs(4326)
    col = next(c for c in ["nombre", "NAME_1", "shapeName", "name", "provincia"]
               if c in lim.columns)
    res = lim[col].map(clasificar)
    lim["provincia"] = [r[0] for r in res]
    lim["region"] = [r[1] for r in res]
    pts = gpd.GeoDataFrame(
        out, geometry=gpd.points_from_xy(out["longitud"], out["latitud"]), crs=4326)
    j = gpd.sjoin(pts, lim[["provincia", "region", "geometry"]],
                  how="inner", predicate="within")
    out = pd.DataFrame(j[~j.index.duplicated()].drop(columns=["geometry", "index_right"]))

    # mismo criterio de unión que A1: celda de 0,01° por día, gana mayor confianza y FRP
    clave_ev = (out["fecha"].dt.strftime("%Y%m%d") + "_"
                + out["latitud"].round(2).astype(str) + "_"
                + out["longitud"].round(2).astype(str))
    out["_k"] = clave_ev
    out["_p"] = out["confianza"].map({"alta": 1, "nominal": 2, "baja": 3}).fillna(4)
    out = out.sort_values(["_k", "_p", "frp"], ascending=[True, True, False])
    out["es_duplicado"] = out.duplicated("_k", keep="first")
    out = out.drop(columns=["_k", "_p"]).sort_values("fecha")
    out["senal"] = "Sin clasificar"

    for c in ["sensor", "confianza", "satelite", "diurno", "provincia", "region", "senal"]:
        out[c] = out[c].astype(str).astype("category")
    out.to_parquet(SALIDA, index=False)
    print(f"{len(out):,} detecciones guardadas, del {out['fecha'].min():%d/%m/%Y} "
          f"al {out['fecha'].max():%d/%m/%Y}")
    print(out["sensor"].value_counts())


if __name__ == "__main__":
    main()