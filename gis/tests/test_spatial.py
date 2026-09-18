"""Comprehensive unit test suite for CyberCast GIS module.

Verifies:
1. Haversine distance calculation and WGS84 coordinate validation.
2. Candidate ATM selection and proximity filtering.
3. Spatial feature generation (distance_from_crime and nearby_crime_density).
4. Hotspot detection via spatial clustering.
5. Strict GeoJSON FeatureCollection contract adherence (RFC 7946, ML_GIS_CONTRACTS.md §2).
6. Concrete SpatialService interface implementation.
"""

import unittest
import math

from gis.spatial.distance import (
    haversine_distance,
    extract_coordinates,
    EARTH_RADIUS_KM,
)
from gis.spatial.candidate_selection import select_candidate_atms
from gis.spatial.density import (
    compute_spatial_features,
    compute_nearby_crime_density,
)
from gis.spatial.hotspots import detect_spatial_hotspots
from gis.spatial.geojson_builder import (
    build_predictions_geojson,
    categorize_risk,
    format_explanation,
)
from gis.spatial.service import SpatialService
from gis.spatial.interface import SpatialInterface


class TestDistanceAndCoordinates(unittest.TestCase):
    """Tests for coordinate extraction, validation, and Haversine distance."""

    def test_extract_coordinates_dict_lat_lng(self):
        coords = extract_coordinates({"lat": 28.6139, "lng": 77.2090})
        self.assertEqual(coords, (28.6139, 77.2090))

    def test_extract_coordinates_dict_latitude_longitude(self):
        coords = extract_coordinates({"latitude": 19.0760, "longitude": 72.8777})
        self.assertEqual(coords, (19.0760, 72.8777))

    def test_extract_coordinates_nested_location(self):
        coords = extract_coordinates({"location": {"lat": 12.9716, "lng": 77.5946}})
        self.assertEqual(coords, (12.9716, 77.5946))

    def test_extract_coordinates_tuple(self):
        coords = extract_coordinates((13.0827, 80.2707))
        self.assertEqual(coords, (13.0827, 80.2707))

    def test_extract_coordinates_invalid_bounds(self):
        # Latitude out of bounds
        with self.assertRaises(ValueError):
            extract_coordinates({"lat": 95.0, "lng": 77.0})
        with self.assertRaises(ValueError):
            extract_coordinates({"lat": -91.0, "lng": 77.0})

        # Longitude out of bounds
        with self.assertRaises(ValueError):
            extract_coordinates({"lat": 28.0, "lng": 185.0})
        with self.assertRaises(ValueError):
            extract_coordinates({"lat": 28.0, "lng": -181.0})

    def test_extract_coordinates_invalid_types(self):
        with self.assertRaises(ValueError):
            extract_coordinates(None)
        with self.assertRaises(ValueError):
            extract_coordinates({"lat": "invalid", "lng": 77.0})
        with self.assertRaises(ValueError):
            extract_coordinates({"lat": float("nan"), "lng": 77.0})

    def test_haversine_same_point(self):
        pt = {"lat": 28.6139, "lng": 77.2090}
        self.assertEqual(haversine_distance(pt, pt), 0.0)

    def test_haversine_known_distance_delhi_mumbai(self):
        # Delhi to Mumbai distance is approximately 1148 km
        delhi = {"lat": 28.6139, "lng": 77.2090}
        mumbai = {"lat": 19.0760, "lng": 72.8777}
        dist = haversine_distance(delhi, mumbai)
        self.assertAlmostEqual(dist, 1148.0, delta=20.0)

    def test_haversine_short_distance(self):
        # 1 degree latitude at equator is approx 111.19 km
        p1 = (0.0, 0.0)
        p2 = (1.0, 0.0)
        dist = haversine_distance(p1, p2)
        expected = (2.0 * math.pi * EARTH_RADIUS_KM) / 360.0
        self.assertAlmostEqual(dist, expected, delta=0.5)


class TestCandidateSelection(unittest.TestCase):
    """Tests for proximity candidate selection."""

    def setUp(self):
        # Base crime location: Connaught Place, New Delhi
        self.crime = {"lat": 28.6315, "lng": 77.2167}

        # Simulated ATMs at various distances
        self.atms = [
            # ~0.5 km away (inside 5 km radius)
            {"atm_id": "ATM-1", "location": {"lat": 28.6350, "lng": 77.2180}, "bank": "SBI", "area": "CP"},
            # ~2.0 km away (inside 5 km radius)
            {"atm_id": "ATM-2", "location": {"lat": 28.6200, "lng": 77.2100}, "bank": "HDFC", "area": "Mandi House"},
            # ~12.0 km away (outside 5 km radius)
            {"atm_id": "ATM-3", "location": {"lat": 28.5355, "lng": 77.2000}, "bank": "ICICI", "area": "Saket"},
            # ATM using flat latitude/longitude format, ~1.0 km away
            {"atm_id": "ATM-4", "latitude": 28.6250, "longitude": 77.2200, "bank": "PNB", "area": "Barakhamba"},
        ]

    def test_select_candidate_atms_default_radius(self):
        candidates = select_candidate_atms(self.crime, radius_km=5.0, atms=self.atms)
        candidate_ids = [c["atm_id"] for c in candidates]

        self.assertIn("ATM-1", candidate_ids)
        self.assertIn("ATM-2", candidate_ids)
        self.assertIn("ATM-4", candidate_ids)
        self.assertNotIn("ATM-3", candidate_ids)  # Saket is outside 5 km

    def test_select_candidate_atms_sorting_by_proximity(self):
        candidates = select_candidate_atms(self.crime, radius_km=5.0, atms=self.atms)
        # Verify sorted ascending by distance to crime
        distances = [
            haversine_distance(self.crime, c["location"])
            for c in candidates
        ]
        self.assertEqual(distances, sorted(distances))

    def test_select_candidate_atms_empty_cases(self):
        # Empty ATM list
        self.assertEqual(select_candidate_atms(self.crime, radius_km=5.0, atms=[]), [])

        # Tight radius with no matches
        candidates = select_candidate_atms(self.crime, radius_km=0.01, atms=self.atms)
        self.assertEqual(candidates, [])

    def test_select_candidate_atms_invalid_radius(self):
        with self.assertRaises(ValueError):
            select_candidate_atms(self.crime, radius_km=-1.0, atms=self.atms)
        with self.assertRaises(ValueError):
            select_candidate_atms(self.crime, radius_km=0.0, atms=self.atms)


class TestDensityAndFeatures(unittest.TestCase):
    """Tests for spatial density and feature computation."""

    def setUp(self):
        self.crime = {"lat": 28.6315, "lng": 77.2167}
        self.atm = {"lat": 28.6350, "lng": 77.2180}

        # Historical crimes near and far from the ATM
        self.historical_crimes = [
            {"crime_id": "C-1", "location": {"lat": 28.6340, "lng": 77.2175}},  # ~0.1 km from ATM
            {"crime_id": "C-2", "location": {"lat": 28.6360, "lng": 77.2190}},  # ~0.15 km from ATM
            {"crime_id": "C-3", "latitude": 28.6400, "longitude": 77.2200},     # ~0.6 km from ATM
            {"crime_id": "C-4", "location": {"lat": 28.5355, "lng": 77.2000}},  # ~12 km from ATM (outside 2 km)
        ]

    def test_compute_nearby_crime_density(self):
        # 3 crimes within 2.0 km, 1 outside
        density = compute_nearby_crime_density(self.atm, self.historical_crimes, density_radius_km=2.0)
        self.assertEqual(density, 3.0)

    def test_compute_nearby_crime_density_empty(self):
        self.assertEqual(compute_nearby_crime_density(self.atm, []), 0.0)

    def test_compute_spatial_features_contract(self):
        features = compute_spatial_features(
            crime_location=self.crime,
            atm_location=self.atm,
            historical_crimes=self.historical_crimes,
            density_radius_km=2.0,
        )

        # Strictly check contract keys
        self.assertIn("distance_from_crime", features)
        self.assertIn("nearby_crime_density", features)
        self.assertIsInstance(features["distance_from_crime"], float)
        self.assertIsInstance(features["nearby_crime_density"], float)
        self.assertGreater(features["distance_from_crime"], 0.0)
        self.assertEqual(features["nearby_crime_density"], 3.0)


class TestHotspots(unittest.TestCase):
    """Tests for spatial clustering and hotspot detection."""

    def test_detect_spatial_hotspots(self):
        # Dense cluster around location A (4 incidents within 0.3 km)
        cluster_a = [
            {"crime_id": "A1", "location": {"lat": 28.6000, "lng": 77.2000}},
            {"crime_id": "A2", "location": {"lat": 28.6010, "lng": 77.2010}},
            {"crime_id": "A3", "location": {"lat": 28.6005, "lng": 77.1995}},
            {"crime_id": "A4", "location": {"lat": 28.6020, "lng": 77.2005}},
        ]
        # Distant noise incident (~30 km away)
        noise = [{"crime_id": "N1", "location": {"lat": 28.3000, "lng": 77.0000}}]

        incidents = cluster_a + noise
        hotspots = detect_spatial_hotspots(incidents, eps_km=1.0, min_samples=3)

        self.assertEqual(len(hotspots), 1)
        hotspot = hotspots[0]
        self.assertEqual(hotspot["cluster_id"], 1)
        self.assertEqual(hotspot["incident_count"], 4)
        self.assertIn("centroid", hotspot)
        self.assertIn("radius_km", hotspot)
        self.assertIn("bounding_box", hotspot)

        # Centroid should be around (28.60, 77.20)
        self.assertAlmostEqual(hotspot["centroid"]["lat"], 28.60, delta=0.01)
        self.assertAlmostEqual(hotspot["centroid"]["lng"], 77.20, delta=0.01)


class TestGeoJsonBuilder(unittest.TestCase):
    """Tests for RFC 7946 GeoJSON FeatureCollection generation and contract adherence."""

    def test_categorize_risk_thresholds(self):
        # ADR-006 / GIS_SPEC thresholds
        self.assertEqual(categorize_risk(0.95), "high")
        self.assertEqual(categorize_risk(0.70), "high")
        self.assertEqual(categorize_risk(0.6999), "medium")
        self.assertEqual(categorize_risk(0.40), "medium")
        self.assertEqual(categorize_risk(0.3999), "low")
        self.assertEqual(categorize_risk(0.0), "low")

    def test_format_explanation_from_strings(self):
        raw = ["High historical risk", "Close to crime location"]
        self.assertEqual(format_explanation(raw), raw)

    def test_format_explanation_from_dicts(self):
        raw = [
            {"feature": "distance_from_crime", "value": 1.25, "contribution": "high"},
            {"feature": "nearby_crime_density", "value": 7.0, "contribution": "medium"},
        ]
        formatted = format_explanation(raw)
        self.assertEqual(len(formatted), 2)
        self.assertIn("1.25 km", formatted[0])
        self.assertIn("7.0 incidents", formatted[1])

    def test_build_predictions_geojson_contract(self):
        predictions = [
            {
                "atm_id": "ATM-9001",
                "location": {"lat": 28.6350, "lng": 77.2180},
                "risk_score": 0.85,
                "confidence": 0.75,
                "predicted_window": {"start": "2026-09-17T12:00:00Z", "end": "2026-09-17T18:00:00Z"},
                "explanation": ["High nearby crime density", "Under 1 km from incident"],
                "bank": "HDFC",
            },
            {
                "atm_id": "ATM-9002",
                "latitude": 28.6200,
                "longitude": 77.2100,
                "risk_score": 0.52,
                "confidence": 0.60,
                "predicted_window": {"start": "2026-09-17T12:00:00Z", "end": "2026-09-17T18:00:00Z"},
                "explanation": [{"feature": "distance_from_crime", "value": 2.1, "contribution": "medium"}],
            },
        ]

        geojson = build_predictions_geojson(predictions)

        # 1. Top-level FeatureCollection check
        self.assertEqual(geojson.get("type"), "FeatureCollection")
        self.assertIn("features", geojson)
        self.assertEqual(len(geojson["features"]), 2)

        # 2. First feature check
        f1 = geojson["features"][0]
        self.assertEqual(f1["type"], "Feature")

        # GeoJSON RFC 7946 strictly requires [longitude, latitude]
        self.assertEqual(f1["geometry"]["type"], "Point")
        self.assertEqual(f1["geometry"]["coordinates"], [77.2180, 28.6350])

        # Properties check strictly matching ML_GIS_CONTRACTS.md §2
        props1 = f1["properties"]
        self.assertEqual(props1["atm_id"], "ATM-9001")
        self.assertEqual(props1["risk_score"], 0.85)
        self.assertEqual(props1["confidence"], 0.75)
        self.assertEqual(props1["risk_category"], "high")
        self.assertEqual(props1["predicted_window"]["start"], "2026-09-17T12:00:00Z")
        self.assertEqual(props1["predicted_window"]["end"], "2026-09-17T18:00:00Z")
        self.assertIsInstance(props1["explanation"], list)
        self.assertEqual(len(props1["explanation"]), 2)

        # 3. Second feature check (medium risk)
        f2 = geojson["features"][1]
        self.assertEqual(f2["geometry"]["coordinates"], [77.2100, 28.6200])
        self.assertEqual(f2["properties"]["risk_category"], "medium")

    def test_build_predictions_geojson_empty(self):
        geojson = build_predictions_geojson([])
        self.assertEqual(geojson, {"type": "FeatureCollection", "features": []})


class TestSpatialService(unittest.TestCase):
    """Tests for the concrete SpatialService class implementing SpatialInterface."""

    def setUp(self):
        self.service: SpatialInterface = SpatialService()
        self.crime = {"lat": 28.6315, "lng": 77.2167}
        self.atms = [
            {"atm_id": "ATM-1", "location": {"lat": 28.6350, "lng": 77.2180}},
            {"atm_id": "ATM-2", "location": {"lat": 28.5000, "lng": 77.1000}},
        ]
        self.crimes = [
            {"crime_id": "C-1", "location": {"lat": 28.6340, "lng": 77.2175}},
        ]

    def test_service_candidate_atms(self):
        candidates = self.service.get_candidate_atms(self.crime, radius_km=5.0, atms=self.atms)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["atm_id"], "ATM-1")

    def test_service_compute_spatial_features(self):
        feats = self.service.compute_spatial_features(
            self.crime, self.atms[0]["location"], self.crimes
        )
        self.assertIn("distance_from_crime", feats)
        self.assertIn("nearby_crime_density", feats)
        self.assertEqual(feats["nearby_crime_density"], 1.0)

    def test_service_to_geojson(self):
        predictions = [
            {
                "atm_id": "ATM-1",
                "location": self.atms[0]["location"],
                "risk_score": 0.8,
                "confidence": 0.6,
                "predicted_window": {"start": "2026-09-17T12:00:00Z", "end": "2026-09-17T18:00:00Z"},
                "explanation": ["Test explanation"],
            }
        ]
        fc = self.service.to_geojson(predictions)
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(len(fc["features"]), 1)


if __name__ == "__main__":
    unittest.main()
