                             
# Voronoi diagram for polygons

[![PyPI version](https://badge.fury.io/py/voronoi-diagram-for-polygons.svg)](https://badge.fury.io/py/voronoi-diagram-for-polygons)
![PyPI - Downloads](https://img.shields.io/pypi/dm/voronoi-diagram-for-polygons)
[![Downloads](https://pepy.tech/badge/voronoi-diagram-for-polygons)](https://pepy.tech/project/voronoi-diagram-for-polygons)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3960407.svg)](https://doi.org/10.5281/zenodo.3960407)

[Voronoi diagram for polygons] is a tool to create a [Voronoi diagram] also known as [Thiessen polygons] for **polygons**. It's based on [Shapely] and [GeoPandas]. There are lots of tools to create a [Voronoi diagram] for points, for example [Create Thiessen Polygons (Analysis)] in [ArcGIS Pro] or [ArcGIS Desktop], [Voronoi Polygons] in [QGIS], or [voronoi_diagram] in [Shapely]. All of them are really cool. How about a [Voronoi diagram] for polygons? That's what this tool does.

<p float="left">
<img width="150" height="150" src="https://github.com/longavailable/voronoi-diagram-for-polygons/raw/master/docs/pics/inputs.png"/>
<img width="150" height="150" src="https://github.com/longavailable/voronoi-diagram-for-polygons/raw/master/docs/pics/outputs.png"/>
</p>

[***Important!***](#dependencies) You have to install or upgrade to the latest developing version of [Shapely] before install [Voronoi diagram for polygons]

## Table of contents
- [Installation, update and uninstallation](#installation--update-and-uninstallation)
	* [Dependencies](#dependencies)
  * [To install](#to-install)
  * [To update](#to-update)
  * [To uninstall](#to-uninstall)
- [Usage](#usage)
- [Known shortages](#known-shortages)
- [How to cite?](#how-to-cite)
- [Changelog](#changelog)

## Installation, update and uninstallation

### Dependencies

***Important!*** It's based on `voronoi_diagram` from [Shapely] which is new in version 1.8.dev0. As of today, it is still a developing version. *(2020-07-26)* You have to install or upgrade to the latest developing version from source firstly:

```bash
pip install git+https://github.com/Toblerity/Shapely
```

```bash
pip install --upgrade git+https://github.com/Toblerity/Shapely
```

### To install

Quick installation with `pip`:
```bash
pip install voronoi-diagram-for-polygons
```
Or from github:
```bash
pip install git+https://github.com/longavailable/voronoi-diagram-for-polygons
```
Also, you can just copy related functions from *[longsgis/longsgis.py]* to your work.

### To update

```bash
pip install --upgrade voronoi-diagram-for-polygons
```

### To uninstall

```bash
pip uninstall voronoi-diagram-for-polygons
```

## Usage

See *[tests/01voronoiDiagram4plg.py]*.
```python
import geopandas as gpd
from longsgis import voronoiDiagram4plg

builtup = gpd.read_file('input.geojson'); builtup.crs = 32650
boundary = gpd.read_file('boundary.geojson'); boundary.crs = 32650
vd = voronoiDiagram4plg(builtup, boundary)
vd.to_file('output.geojson', driver='GeoJSON')
```

## Known shortages

- It may produce multipolygons (consisted by some unconnected polygons) around the boundary.

	<img width="150" height="150" src="https://github.com/longavailable/voronoi-diagram-for-polygons/raw/master/docs/pics/bug001.png"/>

- Special input may cause overlap. See the following:

	<p float="left">
	<img width="300" height="150" src="https://github.com/longavailable/voronoi-diagram-for-polygons/raw/master/docs/pics/bug002_input.png"/>
	<img width="150" height="150" src="https://github.com/longavailable/voronoi-diagram-for-polygons/raw/master/docs/pics/bug002_output.png"/>
	</p>
	
	*To avoid this, I recommend reasonable preprocessing of the input, but use a buffer operation with high-resolution carefully.* A buffer operation with high-resolution will result in circular arcs, which will generate too many vertices in a local area. This may trigger other bugs. In my practices, the following code snippet worked well.
	
```python
def bufferDissolve(gdf, distance, join_style=3):	
	'''Create buffer and dissolve thoese intersects.
	
	Parameters:
		gdf: 
			Type: geopandas.GeoDataFrame
		distance: radius of the buffer
			Type: float
	Returns:
		gdf_bf: buffered and dissolved GeoDataFrame
			Type: geopandas.GeoDataFrame
	'''
	#create buffer and dissolve by invoking `unary_union`
	smp = gdf.buffer(distance, join_style).unary_union
	#convert to GeoSeries and explode to single polygons
	gs = gpd.GeoSeries([smp]).explode()
	#convert to GeoDataFrame
	gdf_bf = gpd.GeoDataFrame(geometry=gs, crs=gdf.crs).reset_index(drop=True)
	return gdf_bf
```

## How to cite

If this tool is useful to your research, 
<a class="github-button" href="https://github.com/longavailable/voronoi-diagram-for-polygons" aria-label="Star longavailable/voronoi-diagram-for-polygons on GitHub">star</a> and cite it as below:
```
Xiaolong Liu, & Meixiu Yu. (2020, July 26). longavailable/voronoi-diagram-for-polygons. Zenodo. 
http://doi.org/10.5281/zenodo.3960407
```
Easily, you can import it to 
<a href="https://www.mendeley.com/import/?url=https://zenodo.org/record/3960407"><i class="fa fa-external-link"></i> Mendeley</a>.

## Changelog

### v0.1.1

- First release.


[Voronoi diagram for polygons]: https://github.com/longavailable/voronoi-diagram-for-polygons
[Voronoi diagram]: https://en.wikipedia.org/wiki/Voronoi_diagram
[Thiessen polygons]: https://en.wikipedia.org/wiki/Voronoi_diagram
[Shapely]: https://shapely.readthedocs.io/en/latest/
[GeoPandas]: https://geopandas.org/index.html
[Create Thiessen Polygons (Analysis)]: https://pro.arcgis.com/en/pro-app/tool-reference/analysis/create-thiessen-polygons.htm
[ArcGIS Pro]: https://www.esri.com/en-us/arcgis/products/arcgis-pro/overview
[ArcGIS Desktop]: https://desktop.arcgis.com/en/
[Voronoi polygons]: https://docs.qgis.org/3.10/en/docs/user_manual/processing_algs/qgis/vectorgeometry.html#voronoi-polygons
[QGIS]: https://qgis.org/en/site/
[voronoi_diagram]: https://shapely.readthedocs.io/en/latest/manual.html?#voronoi-diagram
[longsgis/longsgis.py]: https://github.com/longavailable/voronoi-diagram-for-polygons/raw/master/longsgis/longsgis.py
[tests/01voronoiDiagram4plg.py]: https://github.com/longavailable/voronoi-diagram-for-polygons/raw/master/tests/01voronoiDiagram4plg.py

