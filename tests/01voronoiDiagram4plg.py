import geopandas as gpd
from longsgis import voronoiDiagram4plg

builtup = gpd.read_file('input.geojson'); builtup.crs = 32650
boundary = gpd.read_file('boundary.geojson'); boundary.crs = 32650
vd = voronoiDiagram4plg(builtup, boundary)
vd.to_file('output.geojson', driver='GeoJSON')