"""Unit tests for Coordinate Reference System (CRS) management (Fragment 2).

Verifies:
1. CRS normalization and alias handling for WGS84 (EPSG:4326).
2. WGS84 enforcement and rejection of unauthorized CRS projections.
3. Cross-dataset CRS compatibility validation (preventing crime vs ATM mismatches).
4. WGS84 coordinate boundary validation.
5. Coordinate ordering checks guarding against (lat, lng) vs (lng, lat) inversion.
6. Integration with SpatialPoint, load_crimes, and load_atms.
"""

import unittest

from gis.spatial.crs import (
    DEFAULT_CRS,
    WGS84_CRS,
    GEOJSON_CRS,
    normalize_crs,
    is_wgs84,
    validate_crs,
    validate_crs_compatibility,
    validate_wgs84_bounds,
    check_coordinate_order,
    CRSMismatchError,
    InvalidCRSError,
)
from gis.spatial.data_loader import (
    SpatialPoint,
    prepare_spatial_record,
    load_crimes,
    load_atms,
)


class TestCRSHandling(unittest.TestCase):
    """Tests for CRS normalization and validation."""

    def test_crs_constants(self):
        self.assertEqual(DEFAULT_CRS, "EPSG:4326")
        self.assertEqual(WGS84_CRS, "EPSG:4326")
        self.assertEqual(GEOJSON_CRS, "EPSG:4326")

    def test_normalize_crs_wgs84_aliases(self):
        self.assertEqual(normalize_crs("EPSG:4326"), "EPSG:4326")
        self.assertEqual(normalize_crs("epsg:4326"), "EPSG:4326")
        self.assertEqual(normalize_crs(4326), "EPSG:4326")
        self.assertEqual(normalize_crs("WGS84"), "EPSG:4326")
        self.assertEqual(normalize_crs("wgs 84"), "EPSG:4326")

    def test_normalize_crs_other_projections(self):
        self.assertEqual(normalize_crs("EPSG:3857"), "EPSG:3857")
        self.assertEqual(normalize_crs(32643), "EPSG:32643")

    def test_normalize_crs_invalid(self):
        with self.assertRaises(InvalidCRSError):
            normalize_crs(None)
        with self.assertRaises(InvalidCRSError):
            normalize_crs("")
        with self.assertRaises(InvalidCRSError):
            normalize_crs("   ")

    def test_is_wgs84(self):
        self.assertTrue(is_wgs84("EPSG:4326"))
        self.assertTrue(is_wgs84("WGS84"))
        self.assertTrue(is_wgs84(4326))
        self.assertFalse(is_wgs84("EPSG:3857"))
        self.assertFalse(is_wgs84("EPSG:32643"))
        self.assertFalse(is_wgs84(None))

    def test_validate_crs_allowed(self):
        self.assertEqual(validate_crs("EPSG:4326"), "EPSG:4326")
        self.assertEqual(validate_crs("WGS84"), "EPSG:4326")

    def test_validate_crs_rejected_projections(self):
        # Projected planar CRS are rejected for MVP contract safety
        with self.assertRaises(InvalidCRSError):
            validate_crs("EPSG:3857")
        with self.assertRaises(InvalidCRSError):
            validate_crs("EPSG:32643")
        with self.assertRaises(InvalidCRSError):
            validate_crs("NAD83")

    def test_validate_crs_compatibility_matching(self):
        # Should succeed silently
        validate_crs_compatibility("EPSG:4326", "EPSG:4326")
        validate_crs_compatibility("WGS84", 4326)
        validate_crs_compatibility(None, None)

    def test_validate_crs_compatibility_mismatch(self):
        with self.assertRaises(CRSMismatchError):
            validate_crs_compatibility("EPSG:4326", "EPSG:3857")
        with self.assertRaises(CRSMismatchError):
            validate_crs_compatibility("EPSG:4326", "EPSG:32643", context="candidate search")


class TestCoordinateOrderAndBounds(unittest.TestCase):
    """Tests for coordinate bounds and axis order validation."""

    def test_validate_wgs84_bounds_valid(self):
        # Delhi coordinates: (lat 28.6, lng 77.2)
        validate_wgs84_bounds(lat=28.6139, lng=77.2090)
        # Extreme valid boundaries
        validate_wgs84_bounds(lat=90.0, lng=180.0)
        validate_wgs84_bounds(lat=-90.0, lng=-180.0)

    def test_validate_wgs84_bounds_invalid(self):
        with self.assertRaises(ValueError):
            validate_wgs84_bounds(lat=95.0, lng=77.2)
        with self.assertRaises(ValueError):
            validate_wgs84_bounds(lat=28.6, lng=185.0)

    def test_check_coordinate_order_geojson(self):
        # GeoJSON expects [longitude, latitude]
        coords = [77.2090, 28.6139]
        lat, lng = check_coordinate_order(coords, expected_format="geojson")
        self.assertEqual(lat, 28.6139)
        self.assertEqual(lng, 77.2090)

    def test_check_coordinate_order_geographic(self):
        # Geographic expects (latitude, longitude)
        coords = (28.6139, 77.2090)
        lat, lng = check_coordinate_order(coords, expected_format="geographic")
        self.assertEqual(lat, 28.6139)
        self.assertEqual(lng, 77.2090)

    def test_check_coordinate_order_inversion_detected(self):
        # If [lat=77.2, lng=150.0] is mistakenly passed as GeoJSON [lng, lat],
        # then second element is 150.0 which exceeds latitude max 90.0!
        with self.assertRaises(ValueError):
            check_coordinate_order([28.6139, 120.0], expected_format="geojson")


class TestDataLoaderCRSIntegration(unittest.TestCase):
    """Tests verifying CRS tagging and enforcement in data loading."""

    def test_spatial_point_crs_attribute(self):
        pt = SpatialPoint(x=77.2090, y=28.6139)
        self.assertEqual(pt.crs, "EPSG:4326")

        # Unsupported CRS in SpatialPoint raises InvalidCRSError
        with self.assertRaises(InvalidCRSError):
            SpatialPoint(x=77.2090, y=28.6139, crs="EPSG:3857")

    def test_prepare_spatial_record_crs(self):
        raw = {"crime_id": "c-1", "lat": 28.6, "lng": 77.2}
        prepared = prepare_spatial_record(raw)
        self.assertIsNotNone(prepared)
        self.assertEqual(prepared["crs"], "EPSG:4326")
        self.assertEqual(prepared["geometry"].crs, "EPSG:4326")

        # Unsupported CRS in record raises error in strict mode
        with self.assertRaises(InvalidCRSError):
            prepare_spatial_record(raw, strict=True, crs="EPSG:3857")

    def test_load_crimes_with_crs_validation(self):
        raw = [{"crime_id": "c-1", "lat": 28.6, "lng": 77.2}]
        # Default WGS84 loads cleanly
        crimes = load_crimes(raw, source_crs="EPSG:4326")
        self.assertEqual(len(crimes), 1)
        self.assertEqual(crimes[0]["crs"], "EPSG:4326")

        # Incompatible source CRS is rejected
        with self.assertRaises(InvalidCRSError):
            load_crimes(raw, source_crs="EPSG:3857")

    def test_load_atms_with_crs_validation(self):
        raw = [{"atm_id": "a-1", "lat": 28.6, "lng": 77.2, "bank": "SBI"}]
        atms = load_atms(raw, source_crs="WGS84")
        self.assertEqual(len(atms), 1)
        self.assertEqual(atms[0]["crs"], "EPSG:4326")

        with self.assertRaises(InvalidCRSError):
            load_atms(raw, source_crs="EPSG:32643")


if __name__ == "__main__":
    unittest.main()
