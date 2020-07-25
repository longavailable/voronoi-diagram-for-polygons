# -*- coding: utf-8 -*-
"""
* Updated on 2020/07/25
* python3
**
* Geoprocessing in Python
"""
import geopandas as gpd
from shapely.ops import voronoi_diagram as svd
from shapely.geometry import Polygon, MultiPolygon

def voronoiDiagram4plg(gdf, mask):
	'''Create Voronoi diagram / Thiessen polygons based on polygons.
	
	Parameters:
		gdf: polygons to be used to create Voronoi diagram
			Type: geopandas.GeoDataFrame
		mask: polygon vector used to clip the created Voronoi diagram
			Type: GeoDataFrame, GeoSeries, (Multi)Polygon
	Returns:
		gdf_vd: Thiessen polygons
			Type: geopandas.geodataframe.GeoDataFrame
	'''
	gdf.reset_index(drop=True)
	#convert to shapely.geometry.MultiPolygon
	smp = gdf.unary_union
	#create primary voronoi diagram by invoking shapely.ops.voronoi_diagram (new in Shapely 1.8.dev0)
	smp_vd = svd(smp)
	#convert to GeoSeries and explode to single polygons
	#note that it is NOT supported to GeoDataFrame directly
	gs = gpd.GeoSeries([smp_vd]).explode()
	#convert to GeoDataFrame
	#note that if gdf was shapely.geometry.MultiPolygon, it has no attribute 'crs'
	gdf_vd_primary = gpd.geodataframe.GeoDataFrame(geometry=gs, crs=gdf.crs)
	
	#reset index
	gdf_vd_primary.reset_index(drop=True)	#append(gdf)
	#spatial join by intersecting and dissolve by `index_right`
	gdf_temp = ( gpd.sjoin(gdf_vd_primary, gdf, how='inner', op='intersects')
		.dissolve(by='index_right').reset_index(drop=True) )
	gdf_vd = gpd.clip(gdf_temp, mask)
	gdf_vd = dropHoles(gdf_vd)
	return gdf_vd

def dropHolesBase(plg):
	'''Basic function to remove / drop / fill the holes.
	
	Parameters:
		plg: plg who has holes / empties
			Type: shapely.geometry.MultiPolygon or shapely.geometry.Polygon
	Returns:
		a shapely.geometry.MultiPolygon or shapely.geometry.Polygon object
	'''
	if isinstance(plg, MultiPolygon):
		return MultiPolygon(Polygon(p.exterior) for p in plg)
	elif isinstance(plg, Polygon):
		return Polygon(plg.exterior)

def dropHoles(gdf):
	'''Remove / drop / fill the holes / empties for iterms in GeoDataFrame.
	
	Parameters:
		gdf:
			Type: geopandas.GeoDataFrame
	Returns:
		gdf_nohole: GeoDataFrame without holes
			Type: geopandas.GeoDataFrame
	'''
	gdf_nohole = gpd.GeoDataFrame()
	for g in gdf['geometry']:
		geo = gpd.GeoDataFrame(geometry=gpd.GeoSeries(dropHolesBase(g)))
		gdf_nohole=gdf_nohole.append(geo,ignore_index=True)
	gdf_nohole.rename(columns={gdf_nohole.columns[0]:'geometry'}, inplace=True)
	gdf_nohole.crs = gdf.crs
	return gdf_nohole