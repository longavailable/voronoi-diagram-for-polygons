"""Finds the approximate voronoi diagram generated around a polygon.

Forked from https://github.com/longavailable/voronoi-diagram-for-polygons and last
updated on 2024/12/09. Updated from source 2024/12/09.
"""

import itertools
import math
from typing import Union

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import voronoi_diagram as svd


def minimum_distance(gdf: gpd.GeoDataFrame) -> float:
    """Calculate the minimum distance of all vertices of input geometries.

    Args:
        gdf (geopandas.GeoDataFrame): Polygons to be used.

    Returns:
        float: The minimum distance.
    """
    smp = gdf.unary_union  # convert to shapely.geometry.MultiPolygon
    vertices = []

    if isinstance(smp, shapely.Polygon):
        coords = np.dstack(smp.exterior.coords.xy).tolist()[0]
        vertices.extend(coords)
    else:
        for g in smp.geoms:
            coords = np.dstack(g.exterior.coords.xy).tolist()[0]
            vertices.extend(coords)
    potentials = list(itertools.combinations(vertices, 2))  # pairs of vertices
    all_distance = [
        math.sqrt((pp[0][0] - pp[1][0]) ** 2 + (pp[0][1] - pp[1][1]) ** 2)
        for pp in potentials
    ]  # calculate distance for each pair of vertices
    nonzero_distance = [d for d in all_distance if d > 0.0]  # drop zeros
    return min(nonzero_distance)


def _pnts_on_line_(a: np.ndarray, spacing: float = 1.0, is_percent: bool = False):
    """Add points, at a fixed spacing, to an array representing a line.

    Sourced from https://stackoverflow.com/a/65008592/12371819.

    Args:
        a (numpy.ndarray): A sequence of points, x,y pairs, representing the bounds of a polygon or polyline object.
        spacing (float, optional): Spacing between the points to be added to the line. Defaults to 1.
        is_percent (bool, optional): Express the densification as a percent of the total length. Defaults to False.

    Returns:
        numpy.ndarray: Densified array of points.
    """
    n = len(a) - 1  # segments
    dxdy = a[1:, :] - a[:-1, :]  # coordinate differences
    leng = np.sqrt(np.einsum("ij,ij->i", dxdy, dxdy))  # segment lengths
    if is_percent:  # as percentage
        spacing = abs(spacing)
        spacing = min(spacing / 100, 1.0)
        steps = (sum(leng) * spacing) / leng  # step distance
    else:
        steps = leng / spacing  # step distance
    deltas = dxdy / (steps.reshape(-1, 1))  # coordinate steps
    pnts = np.empty((n,), dtype="O")  # construct an `O` array
    for i in range(n):  # cycle through the segments and make
        num = np.arange(steps[i])  # the new points
        pnts[i] = np.array((num, num)).T * deltas[i] + a[i]
    a0 = a[-1].reshape(1, -1)  # add the final point and concatenate
    return np.concatenate((*pnts, a0), axis=0)


def densify_polygon(gdf: gpd.GeoDataFrame, spacing="auto") -> gpd.GeoDataFrame:  # noqa: ANN001
    """Densify the vertex along the edge of polygon(s).

    Args:
        gdf (geopandas.GeoDataFrame): Polygons to be used.
        spacing (str, int, float, optional): Type or distance to be used. Defaults to 'auto'.

    Returns:
        geopandas.GeoDataFrame: A set of new polygon(s) with more vertices.

    Raises:
        ValueError: If spacing is not a string, int, or float.
    """
    if not isinstance(spacing, (str, float, int)):
        msg = "Spacing must be a string, int, or float."
        raise TypeError(msg)

    if isinstance(spacing, str) and spacing.upper() == "AUTO":
        spacing = 0.25 * minimum_distance(gdf)  # less than 0.5? The less, the better?

    # Create a geoseries containing lists of exterior points
    ext_list = gdf["geometry"].map(lambda g: list(g.exterior.coords))

    # Add points to boundary of polygon
    gdf["geometry"] = ext_list.map(
        lambda x: Polygon(_pnts_on_line_(np.array(x), spacing=spacing)),
    )

    # Drop the temp exterior point column
    return gdf


def voronoiDiagram4plg(  # noqa: N802
    gdf: gpd.GeoDataFrame,
    mask,  # noqa: ANN001
    densify: bool = False,
    spacing="auto",  # noqa: ANN001
) -> gpd.GeoDataFrame:
    """Create Voronoi diagram / Thiessen polygons based on polygons.

    Works on a copy of the input GeoDataFrame.

    Args:
        gdf (geopandas.GeoDataFrame): Polygons to be used to create Voronoi diagram.
        mask (GeoDataFrame, GeoSeries, (Multi)Polygon): Polygon vector used to clip the created Voronoi diagram.
        densify (bool, optional): Whether to densify the polygons. Defaults to False.
        spacing (str, int, float, optional): Spacing for densification. Defaults to 'auto'.

    Returns:
        geopandas.GeoDataFrame: Thiessen polygons.
    """
    gdf = gdf.copy()
    if densify:
        gdf = densify_polygon(gdf, spacing=spacing)
    gdf.reset_index(drop=True)

    # convert to shapely.geometry.MultiPolygon
    smp = gdf.unary_union

    # create primary voronoi diagram by invoking shapely.ops.voronoi_diagram (new in Shapely 1.8.dev0)
    smp_vd = svd(smp)

    # convert to GeoSeries and explode to single polygons
    # note that it is NOT supported to GeoDataFrame directly
    gs = gpd.GeoSeries([smp_vd]).explode(index_parts=True)

    # Fix any invalid polygons
    gs.loc[~gs.is_valid] = gs.loc[~gs.is_valid].apply(lambda geom: geom.buffer(0))

    # convert to GeoDataFrame
    # note that if gdf was shapely.geometry.MultiPolygon, it has no attribute 'crs'
    gdf_vd_primary = gpd.geodataframe.GeoDataFrame(geometry=gs, crs=gdf.crs)

    # reset index
    gdf_vd_primary.reset_index(drop=True)  # append(gdf)

    # spatial join by intersecting and dissolve by `index_right`
    gdf_temp = (
        gpd.sjoin(gdf_vd_primary, gdf, how="inner", predicate="intersects")
        .dissolve(by="index_right")
        .reset_index(drop=True)
    )
    gdf_vd = gpd.clip(gdf_temp, mask)
    gdf_vd["geometry"] = gdf_vd["geometry"].map(dropHoles)
    return gdf_vd


def dropHoles(  # noqa: N802
    plg: Union[shapely.geometry.MultiPolygon, shapely.geometry.Polygon],
) -> Union[shapely.geometry.MultiPolygon, shapely.geometry.Polygon]:
    """Basic function to remove / drop / fill the holes.

    Args:
        plg (shapely.geometry.MultiPolygon or shapely.geometry.Polygon): Polygon with holes.

    Returns:
        shapely.geometry.MultiPolygon or shapely.geometry.Polygon: Polygon without holes.
    """
    if isinstance(plg, MultiPolygon):
        if shapely.__version__ < "2.0":
            return MultiPolygon(Polygon(p.exterior) for p in plg)
        return MultiPolygon(Polygon(p.exterior) for p in plg.geoms)

    if isinstance(plg, Polygon):
        return Polygon(plg.exterior)
    return None
