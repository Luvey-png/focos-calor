import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from agregar_provincias import clasificar, LIMITES

lim = gpd.read_file(LIMITES).to_crs(4326)
col = next(c for c in ["nombre", "NAME_1", "shapeName", "name", "provincia"]
           if c in lim.columns)
# recorta al mismo rectángulo que los datos (saca el sector antártico)
lim = gpd.clip(lim, box(-73.6, -55.1, -53.6, -21.7))
lim["provincia"] = [clasificar(n)[0] for n in lim[col]]
lim = lim.to_crs("ESRI:102033")  # proyección de áreas iguales para Sudamérica
lim["km2"] = lim.geometry.area / 1e6
out = lim.groupby("provincia", as_index=False)["km2"].sum().round(0)
out.to_csv("data/superficies.csv", index=False)
print(out.sort_values("km2", ascending=False).to_string(index=False))