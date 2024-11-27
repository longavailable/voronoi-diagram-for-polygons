# -*- coding: utf-8 -*-
"""
* Updated on 2023/04/17
* python3
**
* Geoprocessing in Python
"""
import pandas as pd
import geopandas as gpd
import numpy as np
import shapely
from shapely.ops import voronoi_diagram as svd
from shapely.geometry import Polygon, MultiPolygon
import itertools, math

def minimum_distance(gdf):
	'''Calculate the minimum distance of all vertices of input geometries.
	
	Parameters:
		gdf: polygons to be used
			Type: geopandas.GeoDataFrame
	Returns:
		A float for the minimum distance.
	'''
	smp = gdf.unary_union	# convert to shapely.geometry.MultiPolygon
	vertices = []
	for g in smp.geoms:
		coords = np.dstack(g.exterior.coords.xy).tolist()[0]	# vertices of each geometry
		vertices = vertices + coords
	potentials = list(itertools.combinations(vertices,2))	# pairs of vertices
	all_distance = [math.sqrt((pp[0][0]-pp[1][0])**2+(pp[0][1]-pp[1][1])**2) for pp in potentials]	# calculate distance for each pair of vertices
	nonzero_distance = [d for d in all_distance if d>0.0]	# drop zeros
	return min(nonzero_distance)
	
def _pnts_on_line_(a, spacing=1, is_percent=False):  # densify by distance
	"""Add points, at a fixed spacing, to an array representing a line.
	Sourced from https://stackoverflow.com/a/65008592/12371819

	**See**  `densify_by_distance` for documentation.

	Parameters
	----------
	a : array
		A sequence of `points`, x,y pairs, representing the bounds of a polygon
		or polyline object.
	spacing : number
		Spacing between the points to be added to the line.
	is_percent : boolean
		Express the densification as a percent of the total length.

	Notes
	-----
	Called by `pnt_on_poly`.
	"""
	N = len(a) - 1                                    # segments
	dxdy = a[1:, :] - a[:-1, :]                       # coordinate differences
	leng = np.sqrt(np.einsum('ij,ij->i', dxdy, dxdy))  # segment lengths
	if is_percent:                                    # as percentage
		spacing = abs(spacing)
		spacing = min(spacing / 100, 1.)
		steps = (sum(leng) * spacing) / leng          # step distance
	else:
		steps = leng / spacing                        # step distance
	deltas = dxdy / (steps.reshape(-1, 1))            # coordinate steps
	pnts = np.empty((N,), dtype='O')                  # construct an `O` array
	for i in range(N):              # cycle through the segments and make
		num = np.arange(steps[i])   # the new points
		pnts[i] = np.array((num, num)).T * deltas[i] + a[i]
	a0 = a[-1].reshape(1, -1)       # add the final point and concatenate
	return np.concatenate((*pnts, a0), axis=0)

def densify_polygon(gdf, spacing='auto'):
	'''Densify the vertex along the edge of polygon(s).
	
	Parameters:
		gdf: polygons to be used
			Type: geopandas.GeoDataFrame
		spacing: type or distance to be used
			Type: string, int, or float
	Returns:
		A set of new polygon(s) with more vertices.
		Type: geopandas.GeoDataFrame
	'''
	if isinstance(spacing, (str, float, int)):
		if isinstance(spacing, str) and spacing.upper() == 'AUTO':
			spacing = 0.25 * minimum_distance(gdf)	# less than 0.5? The less, the better?
		smp = gdf.unary_union	# convert to shapely.geometry.MultiPolygon
		all_coords = []
		for g in smp.geoms:
			coords=np.dstack(g.exterior.coords.xy).tolist()	# vertices of each geometry
			all_coords.append(*coords)
			
		polygons = []
		for i, p in enumerate(all_coords):
			new_polygon = Polygon(_pnts_on_line_(np.array(p),spacing=spacing))	# densify each polygon
			polygons.append(new_polygon)
		return gpd.GeoDataFrame({'geometry': polygons}, crs=gdf.crs)

def voronoiDiagram4plg(gdf, mask, densify=False, spacing='auto'):
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
	if densify: gdf = densify_polygon(gdf, spacing=spacing)
	gdf.reset_index(drop=True)
	#convert to shapely.geometry.MultiPolygon
	smp = gdf.unary_union
	#create primary voronoi diagram by invoking shapely.ops.voronoi_diagram (new in Shapely 1.8.dev0)
	smp_vd = svd(smp)
	#convert to GeoSeries and explode to single polygons
	#note that it is NOT supported to GeoDataFrame directly
	gs = gpd.GeoSeries([smp_vd]).explode(index_parts=True)
	#convert to GeoDataFrame
	#note that if gdf was shapely.geometry.MultiPolygon, it has no attribute 'crs'
	gdf_vd_primary = gpd.geodataframe.GeoDataFrame(geometry=gs, crs=gdf.crs)
	
	#reset index
	gdf_vd_primary.reset_index(drop=True)	#append(gdf)
	#spatial join by intersecting and dissolve by `index_right`
	gdf_temp = ( gpd.sjoin(gdf_vd_primary, gdf, how='inner', predicate='intersects')
		.dissolve(by='index_right').reset_index(drop=True) )
	gdf_vd = gpd.clip(gdf_temp, mask)
	gdf_vd['geometry'] = gdf_vd['geometry'].map(dropHoles)
	return gdf_vd

def dropHoles(plg):
	'''Basic function to remove / drop / fill the holes.
	
	Parameters:
		plg: plg who has holes / empties
			Type: shapely.geometry.MultiPolygon or shapely.geometry.Polygon
	Returns:
		a shapely.geometry.MultiPolygon or shapely.geometry.Polygon object
	'''
	if isinstance(plg, MultiPolygon):
		if shapely.__version__ < '2.0':
			return MultiPolygon(Polygon(p.exterior) for p in plg)
		else:
			return MultiPolygon(Polygon(p.exterior) for p in plg.geoms)
	elif isinstance(plg, Polygon):
		return Polygon(plg.exterior)

