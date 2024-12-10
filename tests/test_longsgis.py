import unittest
import warnings

import geopandas as gpd
from shapely.geometry import Polygon

from longsgis import densify_polygon


class TestDensifyPolygon(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter(
            "ignore",
            category=DeprecationWarning,
        )  # HACK geopandas warning suppression for testing

    def test_densify_polygon(self):
        # Create a sample GeoDataFrame with a simple polygon
        p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]).normalize()
        p2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]).normalize()
        gdf = gpd.GeoDataFrame(
            {"geometry": [p1, p2], "test_col1": ["a", "b"], "test_col2": ["c", "d"]},
            crs="EPSG:3857",
        )

        densified_gdf = densify_polygon(gdf.copy(), spacing=0.1)

        # Original columns should be preservered
        self.assertTrue(all(col in densified_gdf.columns for col in gdf.columns))

        # Check that the densified polygons are correct
        for i, r in densified_gdf.iterrows():
            with self.subTest(i=i, r=r):
                densified = r["geometry"]
                original = gdf.iloc[i]["geometry"]

                # Densified polygons should be valid, simple, and have the same area
                self.assertTrue(densified.is_valid)
                self.assertTrue(densified.is_simple)
                self.assertAlmostEqual(densified.area, original.area)

                # Polygons should be the same (after simplification)
                simplified_densified = densified.simplify(
                    tolerance=0.01, preserve_topology=True
                ).normalize()
                self.assertTrue(
                    simplified_densified.equals_exact(original, tolerance=1e-6)
                )

                # Densified polygons should have more vertices
                self.assertGreater(
                    len(densified.exterior.coords), len(original.exterior.coords)
                )
