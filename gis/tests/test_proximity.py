"""Unit tests for crime-to-ATM proximity analysis (Fragment 3).

Verifies:
1. calculate_crime_atm_distance point-to-point metric calculations.
2. select_candidate_atms proximity filtering with configurable radius.
3. Explicit distance units (kilometers / km) and rounding precision.
4. Deterministic sorting with tie-breaking by atm_id.
5. Contract and schema preservation (ML_GIS_CONTRACTS.md §1 spatial_features).
6. Safe handling of missing/corrupt coordinates and out-of-bounds inputs.
7. Rejection of non-positive radius or mismatched CRS.
"""

import unittest

from gis.spatial.candidate_selection import (
    calculate_crime_atm_distance,
    select_candidate_atms,
    DEFAULT_SEARCH_RADIUS_KM,
    DISTANCE_UNIT,
)
from gis.spatial.crs import CRSMismatchError
from gis.spatial.density import compute_spatial_features


class TestCrimeATMProximityAnalysis(unittest.TestCase):
    """Tests for crime-to-ATM proximity and distance calculations."""

    def setUp(self):
        # Reported crime location: Connaught Place, New Delhi (WGS84 EPSG:4326)
        self.crime = {"lat": 28.6315, "lng": 77.2167}

        # Candidate ATMs in Delhi NCR
        self.atms = [
            {
                "atm_id": "ATM-CP-01",
                "location": {"lat": 28.6350, "lng": 77.2180},
                "bank": "SBI",
                "area": "Connaught Place",
                "historical_risk_score": 0.85,
            },
            {
                "atm_id": "ATM-MH-02",
                "location": {"lat": 28.6200, "lng": 77.2100},
                "bank": "HDFC",
                "area": "Mandi House",
                "historical_risk_score": 0.45,
            },
            {
                "atm_id": "ATM-NOIDA-03",
                "location": {"lat": 28.5700, "lng": 77.3200},
                "bank": "ICICI",
                "area": "Noida Sector 18",
                "historical_risk_score": 0.60,
            },
            {
                "atm_id": "ATM-GGN-04",
                "location": {"lat": 28.4595, "lng": 77.0266},
                "bank": "Axis",
                "area": "Cyber City Gurgaon",
                "historical_risk_score": 0.70,
            },
        ]

    def test_calculate_crime_atm_distance_valid(self):
        # Crime to ATM-CP-01: approx 0.41 km
        dist = calculate_crime_atm_distance(self.crime, self.atms[0]["location"])
        self.assertIsInstance(dist, float)
        self.assertAlmostEqual(dist, 0.41, delta=0.05)

        # Crime to ATM-MH-02: approx 1.44 km
        dist_mh = calculate_crime_atm_distance(self.crime, self.atms[1]["location"])
        self.assertAlmostEqual(dist_mh, 1.44, delta=0.05)

        # Crime to ATM-NOIDA-03: approx 12.2 km
        dist_noida = calculate_crime_atm_distance(self.crime, self.atms[2]["location"])
        self.assertAlmostEqual(dist_noida, 12.2, delta=0.5)

    def test_calculate_crime_atm_distance_same_point(self):
        # Distance from point to itself must be strictly 0.0 km
        dist = calculate_crime_atm_distance(self.crime, self.crime)
        self.assertEqual(dist, 0.0)

    def test_calculate_crime_atm_distance_invalid_inputs(self):
        # Null coordinates
        with self.assertRaises(ValueError):
            calculate_crime_atm_distance(None, self.crime)
        with self.assertRaises(ValueError):
            calculate_crime_atm_distance(self.crime, None)

        # Out-of-bounds latitude (> 90.0)
        with self.assertRaises(ValueError):
            calculate_crime_atm_distance({"lat": 95.0, "lng": 77.0}, self.crime)

        # NaN coordinates
        with self.assertRaises(ValueError):
            calculate_crime_atm_distance({"lat": float("nan"), "lng": 77.0}, self.crime)

    def test_select_candidate_atms_default_radius(self):
        # Default radius is 5.0 km (from docs/GIS_SPEC.md)
        self.assertEqual(DEFAULT_SEARCH_RADIUS_KM, 5.0)

        candidates = select_candidate_atms(self.crime, atms=self.atms)
        candidate_ids = [c["atm_id"] for c in candidates]

        # CP (~0.4 km) and Mandi House (~1.4 km) are within 5 km
        self.assertIn("ATM-CP-01", candidate_ids)
        self.assertIn("ATM-MH-02", candidate_ids)

        # Noida (~12 km) and Gurgaon (~27 km) are outside 5 km
        self.assertNotIn("ATM-NOIDA-03", candidate_ids)
        self.assertNotIn("ATM-GGN-04", candidate_ids)

    def test_select_candidate_atms_configurable_radius(self):
        # 1.0 km radius: only ATM-CP-01 matches
        cand_1km = select_candidate_atms(self.crime, radius_km=1.0, atms=self.atms)
        self.assertEqual(len(cand_1km), 1)
        self.assertEqual(cand_1km[0]["atm_id"], "ATM-CP-01")

        # 15.0 km radius: includes Noida, but excludes Gurgaon (~27 km)
        cand_15km = select_candidate_atms(self.crime, radius_km=15.0, atms=self.atms)
        ids_15km = [c["atm_id"] for c in cand_15km]
        self.assertEqual(len(cand_15km), 3)
        self.assertIn("ATM-NOIDA-03", ids_15km)
        self.assertNotIn("ATM-GGN-04", ids_15km)

        # None radius: returns all ATMs computed and sorted by distance
        cand_all = select_candidate_atms(self.crime, radius_km=None, atms=self.atms)
        self.assertEqual(len(cand_all), 4)

    def test_select_candidate_atms_deterministic_sorting(self):
        # Two ATMs at exactly the same location/distance
        tied_atms = [
            {"atm_id": "ATM-ZETA", "location": {"lat": 28.6350, "lng": 77.2180}},
            {"atm_id": "ATM-ALPHA", "location": {"lat": 28.6350, "lng": 77.2180}},
        ]
        candidates = select_candidate_atms(self.crime, radius_km=5.0, atms=tied_atms)
        # Should be deterministically sorted by atm_id when distance is tied
        self.assertEqual(candidates[0]["atm_id"], "ATM-ALPHA")
        self.assertEqual(candidates[1]["atm_id"], "ATM-ZETA")

    def test_schema_and_contract_preservation(self):
        candidates = select_candidate_atms(self.crime, radius_km=5.0, atms=self.atms)
        self.assertGreater(len(candidates), 0)

        first = candidates[0]
        # Preserves original metadata
        self.assertEqual(first["bank"], "SBI")
        self.assertEqual(first["area"], "Connaught Place")
        self.assertEqual(first["historical_risk_score"], 0.85)

        # Provides explicit metric distance in km (GIS ranking field; unit is also explicit)
        self.assertIn("distance_from_crime_km", first)
        self.assertIsInstance(first["distance_from_crime_km"], float)
        self.assertEqual(first["distance_unit"], DISTANCE_UNIT)
        self.assertEqual(DISTANCE_UNIT, "km")

        # GIS_SPEC: candidate shortlist is before ML spatial_features are attached.
        # Incomplete spatial_features (distance without density) must not be invented here.
        self.assertNotIn("spatial_features", first)

    def test_invalid_radius_raises_value_error(self):
        with self.assertRaises(ValueError):
            select_candidate_atms(self.crime, radius_km=-5.0, atms=self.atms)
        with self.assertRaises(ValueError):
            select_candidate_atms(self.crime, radius_km=0.0, atms=self.atms)

    def test_limit_parameter(self):
        cand = select_candidate_atms(self.crime, radius_km=50.0, atms=self.atms, limit=2)
        self.assertEqual(len(cand), 2)
        # Verify limit <= 0 raises ValueError
        with self.assertRaises(ValueError):
            select_candidate_atms(self.crime, limit=0, atms=self.atms)

    def test_crs_mismatch_detection(self):
        # ATM record with unauthorized/mismatched CRS
        bad_crs_atms = [
            {"atm_id": "ATM-BAD-CRS", "location": {"lat": 28.63, "lng": 77.21}, "crs": "EPSG:3857"}
        ]
        with self.assertRaises(CRSMismatchError):
            select_candidate_atms(self.crime, atms=bad_crs_atms, crime_crs="EPSG:4326")

    def test_safe_handling_of_corrupt_atms(self):
        corrupt_atms = [
            {"atm_id": "ATM-VALID", "location": {"lat": 28.6350, "lng": 77.2180}},
            {"atm_id": "ATM-NULL-COORDS", "latitude": None, "longitude": None},
            {"atm_id": "ATM-NAN-COORDS", "location": {"lat": float("nan"), "lng": 77.0}},
            "non-dict-entry",
        ]
        candidates = select_candidate_atms(self.crime, radius_km=5.0, atms=corrupt_atms)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["atm_id"], "ATM-VALID")

    def test_invalid_crime_location_raises(self):
        with self.assertRaises(ValueError):
            select_candidate_atms(None, radius_km=5.0, atms=self.atms)
        with self.assertRaises(ValueError):
            select_candidate_atms({"lat": float("inf"), "lng": 77.0}, radius_km=5.0, atms=self.atms)
        with self.assertRaises(ValueError):
            select_candidate_atms({"lat": 28.63}, radius_km=5.0, atms=self.atms)

    def test_distance_matches_ml_spatial_features_contract(self):
        # Same Haversine kilometer value is consumed as distance_from_crime by ML.
        dist = calculate_crime_atm_distance(self.crime, self.atms[0])
        features = compute_spatial_features(
            crime_location=self.crime,
            atm_location=self.atms[0],
            historical_crimes=[],
        )
        self.assertEqual(features["distance_from_crime"], dist)
        self.assertEqual(features["nearby_crime_density"], 0.0)

    def test_empty_atm_list_returns_empty(self):
        self.assertEqual(select_candidate_atms(self.crime, radius_km=5.0, atms=[]), [])
        self.assertEqual(select_candidate_atms(self.crime, radius_km=5.0, atms=None), [])

    def test_distance_rounding_is_deterministic(self):
        dist_a = calculate_crime_atm_distance(self.crime, self.atms[0]["location"])
        dist_b = calculate_crime_atm_distance(self.crime, self.atms[0]["location"])
        self.assertEqual(dist_a, dist_b)
        # 4 decimal places from haversine_distance
        self.assertEqual(dist_a, round(dist_a, 4))


if __name__ == "__main__":
    unittest.main()
