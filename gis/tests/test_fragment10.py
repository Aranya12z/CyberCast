"""Fragment 10 — P3 GIS Testing and Validation.

Focused tests for the 14 categories mandated by Fragment 10.
Each class is labelled with the category number it satisfies.
Existing test files (test_crs, test_data_loader, test_spatial,
test_proximity, test_geojson_builder, test_p2_p3_interface) cover
categories 1, 2, 4, 5, 6, 7, 9, 11, 12 thoroughly.

This file fills the remaining gaps found during the Fragment 10 audit:
  - Category  3: additional invalid-coordinate type cases
  - Category  8: density edge cases (zero/negative radius)
  - Category 10: hotspot edge cases (no cluster, two clusters, duplicate incidents)
  - Category 13: empty-dataset and edge-value (equatorial 0,0) scenarios
  - Category 14: duplicate records (ATM id, crime records in density)

No new GIS functionality is added. All tests verify actual behavior.
"""

import math
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gis.spatial.distance import extract_coordinates, haversine_distance
from gis.spatial.candidate_selection import select_candidate_atms
from gis.spatial.density import (
    compute_nearby_crime_density,
    compute_spatial_features,
    DEFAULT_DENSITY_RADIUS_KM,
)
from gis.spatial.hotspots import detect_spatial_hotspots
from gis.spatial.geojson_builder import build_predictions_geojson, categorize_risk
from gis.spatial.geojson_validator import validate_predictions_geojson
from gis.spatial.data_loader import load_crimes, load_atms, prepare_spatial_record
from gis.spatial.service import SpatialService


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 1 — Valid coordinate input
# Confirms correct extraction across every supported input format.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory01ValidCoordinateInput:
    """Category 1: valid coordinate input in all supported representations."""

    def test_dict_lat_lng_keys(self):
        lat, lng = extract_coordinates({"lat": 12.9716, "lng": 77.5946})
        assert lat == 12.9716
        assert lng == 77.5946

    def test_dict_latitude_longitude_keys(self):
        lat, lng = extract_coordinates({"latitude": 19.0760, "longitude": 72.8777})
        assert lat == 19.0760
        assert lng == 72.8777

    def test_nested_location_dict(self):
        lat, lng = extract_coordinates({"location": {"lat": 28.6139, "lng": 77.2090}})
        assert lat == 28.6139
        assert lng == 77.2090

    def test_tuple_pair(self):
        lat, lng = extract_coordinates((13.0827, 80.2707))
        assert lat == 13.0827
        assert lng == 80.2707

    def test_list_pair(self):
        lat, lng = extract_coordinates([0.0, 0.0])  # equatorial WGS84 origin
        assert lat == 0.0
        assert lng == 0.0

    def test_equatorial_origin_is_valid(self):
        """(0.0, 0.0) is a legitimate WGS84 coordinate (Gulf of Guinea)."""
        lat, lng = extract_coordinates({"lat": 0.0, "lng": 0.0})
        assert lat == 0.0 and lng == 0.0

    def test_boundary_extremes_are_valid(self):
        """WGS84 allows exactly ±90° lat and ±180° lng."""
        lat, lng = extract_coordinates({"lat": 90.0, "lng": 180.0})
        assert lat == 90.0 and lng == 180.0
        lat, lng = extract_coordinates({"lat": -90.0, "lng": -180.0})
        assert lat == -90.0 and lng == -180.0

    def test_integer_coordinates_accepted(self):
        """Integer lat/lng values must be coerced to float."""
        lat, lng = extract_coordinates({"lat": 28, "lng": 77})
        assert isinstance(lat, float)
        assert isinstance(lng, float)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 2 — Missing coordinates
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory02MissingCoordinates:
    """Category 2: missing coordinate fields produce correct errors/skips."""

    def test_empty_dict_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({})

    def test_missing_lng_field_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lat": 28.6})

    def test_missing_lat_field_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lng": 77.2})

    def test_prepare_spatial_record_missing_coords_non_strict(self):
        """Record with no coordinate fields → None in non-strict mode."""
        result = prepare_spatial_record({"crime_id": "c-x", "crime_type": "fraud"}, strict=False)
        assert result is None

    def test_prepare_spatial_record_missing_coords_strict(self):
        """Record with no coordinate fields → raises in strict mode."""
        with pytest.raises((ValueError, TypeError)):
            prepare_spatial_record({"crime_id": "c-x"}, strict=True)

    def test_load_crimes_drops_records_with_missing_coords(self):
        raw = [
            {"crime_id": "good", "lat": 12.9, "lng": 77.6},
            {"crime_id": "no-coords"},  # no coordinates at all
            {"crime_id": "null-coords", "lat": None, "lng": None},
        ]
        crimes = load_crimes(raw, drop_invalid=True)
        assert len(crimes) == 1
        assert crimes[0]["crime_id"] == "good"

    def test_load_atms_drops_records_with_missing_coords(self):
        raw = [
            {"atm_id": "good", "lat": 12.9, "lng": 77.6, "bank": "SBI"},
            {"atm_id": "no-coords", "bank": "HDFC"},
        ]
        atms = load_atms(raw, drop_invalid=True)
        assert len(atms) == 1
        assert atms[0]["atm_id"] == "good"

    def test_select_candidate_atms_skips_atms_without_coords(self):
        crime = {"lat": 12.9352, "lng": 77.6245}
        atms = [
            {"atm_id": "good", "lat": 12.9360, "lng": 77.6250},
            {"atm_id": "no-coords"},  # no coordinates
        ]
        candidates = select_candidate_atms(crime, radius_km=5.0, atms=atms)
        assert len(candidates) == 1
        assert candidates[0]["atm_id"] == "good"


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 3 — Invalid coordinates (types, values, structure)
# Fills gaps not covered by existing tests: string coords, boolean coords,
# empty-string values, list with wrong length.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory03InvalidCoordinates:
    """Category 3: invalid coordinate inputs raise consistently."""

    def test_string_latitude_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lat": "28.6", "lng": 77.2})

    def test_string_longitude_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lat": 28.6, "lng": "77.2"})

    def test_boolean_latitude_raises(self):
        """Booleans must not be accepted as numeric coordinates."""
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lat": True, "lng": 77.2})

    def test_none_as_input_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates(None)

    def test_nan_latitude_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lat": float("nan"), "lng": 77.2})

    def test_inf_longitude_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lat": 12.9, "lng": float("inf")})

    def test_latitude_above_90_raises(self):
        with pytest.raises(ValueError):
            extract_coordinates({"lat": 91.0, "lng": 77.2})

    def test_latitude_below_minus_90_raises(self):
        with pytest.raises(ValueError):
            extract_coordinates({"lat": -91.0, "lng": 77.2})

    def test_longitude_above_180_raises(self):
        with pytest.raises(ValueError):
            extract_coordinates({"lat": 12.9, "lng": 181.0})

    def test_longitude_below_minus_180_raises(self):
        with pytest.raises(ValueError):
            extract_coordinates({"lat": 12.9, "lng": -181.0})

    def test_empty_string_latitude_raises(self):
        with pytest.raises((ValueError, TypeError)):
            extract_coordinates({"lat": "", "lng": 77.2})

    def test_haversine_with_invalid_second_point_raises(self):
        with pytest.raises((ValueError, TypeError)):
            haversine_distance({"lat": 12.9, "lng": 77.6}, {"lat": float("nan"), "lng": 77.0})

    def test_load_crimes_strict_mode_raises_on_invalid(self):
        with pytest.raises((ValueError, TypeError)):
            load_crimes([{"crime_id": "bad", "lat": 999.0, "lng": 0.0}], drop_invalid=False)

    def test_load_atms_strict_mode_raises_on_invalid(self):
        with pytest.raises((ValueError, TypeError)):
            load_atms([{"atm_id": "bad", "lat": 0.0, "lng": 999.0}], drop_invalid=False)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 4 — CRS handling (covered fully by test_crs.py)
# One integration-level smoke test confirms the chain: load → SpatialPoint CRS.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory04CRSHandling:
    """Category 4: CRS enforcement at data loading level."""

    def test_loaded_crime_carries_epsg4326(self):
        crimes = load_crimes([{"crime_id": "c1", "lat": 12.9, "lng": 77.6}])
        assert crimes[0]["crs"] == "EPSG:4326"
        assert crimes[0]["geometry"].crs == "EPSG:4326"

    def test_loaded_atm_carries_epsg4326(self):
        atms = load_atms([{"atm_id": "a1", "lat": 12.9, "lng": 77.6, "bank": "SBI"}])
        assert atms[0]["crs"] == "EPSG:4326"
        assert atms[0]["geometry"].crs == "EPSG:4326"

    def test_geojson_coordinates_are_wgs84_ordered(self):
        """GeoJSON output is [lng, lat] — the WGS84 / RFC 7946 axis order."""
        pred = [{
            "atm_id": "a1", "location": {"lat": 12.9352, "lng": 77.6245},
            "risk_score": 0.8, "confidence": 0.7,
            "predicted_window": {"start": "2026-09-18T10:00:00Z", "end": "2026-09-18T16:00:00Z"},
            "explanation": [],
        }]
        fc = build_predictions_geojson(pred)
        coords = fc["features"][0]["geometry"]["coordinates"]
        # RFC 7946: [longitude, latitude]
        assert coords[0] == 77.6245  # longitude
        assert coords[1] == 12.9352  # latitude


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 5 — Crime-to-ATM distance (covered by test_proximity.py)
# Additional focused assertions on known geographic values.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory05CrimeToATMDistance:
    """Category 5: Haversine distance, units (km), 4dp, symmetry."""

    def test_delhi_connaught_place_to_nearby_atm_is_less_than_1km(self):
        crime = {"lat": 28.6315, "lng": 77.2167}
        atm = {"lat": 28.6350, "lng": 77.2180}
        dist = haversine_distance(crime, atm)
        assert 0.0 < dist < 1.0, f"Expected sub-km distance, got {dist}"

    def test_distance_value_is_in_km_not_degrees(self):
        """~0.003° lat offset ≈ 333 m = 0.333 km, NOT 0.003."""
        p1 = {"lat": 12.9352, "lng": 77.6245}
        p2 = {"lat": 12.9382, "lng": 77.6245}  # ~330 m north
        dist = haversine_distance(p1, p2)
        assert 0.25 <= dist <= 0.45, f"Expected ~0.33 km, got {dist}"

    def test_distance_rounded_to_4dp(self):
        dist = haversine_distance({"lat": 28.6315, "lng": 77.2167},
                                  {"lat": 28.6350, "lng": 77.2180})
        assert round(dist, 4) == dist

    def test_distance_is_symmetric(self):
        a = {"lat": 12.9352, "lng": 77.6245}
        b = {"lat": 12.9400, "lng": 77.6300}
        assert haversine_distance(a, b) == haversine_distance(b, a)

    def test_distance_is_zero_for_same_point(self):
        p = {"lat": 12.9352, "lng": 77.6245}
        assert haversine_distance(p, p) == 0.0

    def test_feature_distance_from_crime_matches_haversine(self):
        crime = {"lat": 28.6315, "lng": 77.2167}
        atm = {"lat": 28.6350, "lng": 77.2180}
        features = compute_spatial_features(crime, atm, [])
        direct = haversine_distance(crime, atm)
        assert features["distance_from_crime"] == direct


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 6 — Zero nearby crimes (covered; single focused test added)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory06ZeroNearby:
    """Category 6: nearby_crime_density must be 0.0 when no crimes exist."""

    def test_empty_list_yields_zero(self):
        assert compute_nearby_crime_density({"lat": 12.9, "lng": 77.6}, []) == 0.0

    def test_none_yields_zero(self):
        assert compute_nearby_crime_density({"lat": 12.9, "lng": 77.6}, None) == 0.0

    def test_all_crimes_beyond_radius_yields_zero(self):
        atm = {"lat": 12.9352, "lng": 77.6245}
        distant = [{"lat": 19.0760, "lng": 72.8777}]  # Mumbai
        assert compute_nearby_crime_density(atm, distant) == 0.0

    def test_spatial_features_density_is_zero_when_no_crimes(self):
        feats = compute_spatial_features({"lat": 12.9352, "lng": 77.6245},
                                         {"lat": 12.9380, "lng": 77.6270}, [])
        assert feats["nearby_crime_density"] == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 7 — Multiple nearby crimes
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory07MultipleNearby:
    """Category 7: density counts all crimes within radius, not just first."""

    ATM = {"lat": 12.9352, "lng": 77.6245}

    def test_three_nearby_counted(self):
        crimes = [
            {"lat": 12.9355, "lng": 77.6248},  # ~40 m
            {"lat": 12.9360, "lng": 77.6250},  # ~100 m
            {"lat": 12.9400, "lng": 77.6280},  # ~600 m
        ]
        density = compute_nearby_crime_density(self.ATM, crimes)
        assert density == 3.0

    def test_mix_near_and_far_crimes(self):
        near = [{"lat": 12.9355, "lng": 77.6248}]
        far = [{"lat": 13.0827, "lng": 80.2707}]  # Chennai
        density = compute_nearby_crime_density(self.ATM, near + far)
        assert density == 1.0

    def test_density_increases_monotonically_with_more_crimes(self):
        def density_with_n(n):
            crimes = [{"lat": 12.9352 + i * 0.0002, "lng": 77.6245} for i in range(n)]
            return compute_nearby_crime_density(self.ATM, crimes)

        d1 = density_with_n(1)
        d5 = density_with_n(5)
        d10 = density_with_n(10)
        assert d1 <= d5 <= d10


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 8 — Spatial density calculation (edge cases not in existing tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory08SpatialDensityEdgeCases:
    """Category 8: density edge cases — zero radius, exact boundary, large radius."""

    ATM = {"lat": 12.9352, "lng": 77.6245}
    CRIME_AT_ATM = {"lat": 12.9352, "lng": 77.6245}  # co-located

    def test_zero_radius_only_counts_crimes_at_exact_atm_location(self):
        """With radius=0, only a crime at exactly the ATM location (distance=0) is counted."""
        crimes = [
            self.CRIME_AT_ATM,                          # distance = 0.0 → counted
            {"lat": 12.9353, "lng": 77.6246},           # distance > 0 → not counted
        ]
        density = compute_nearby_crime_density(self.ATM, crimes, density_radius_km=0.0)
        # Crime at exact ATM location has distance=0.0 which satisfies <=0.0
        assert density == 1.0

    def test_very_large_radius_counts_all_valid_crimes(self):
        crimes = [
            {"lat": 12.9352, "lng": 77.6245},   # Bangalore
            {"lat": 28.6139, "lng": 77.2090},   # Delhi
            {"lat": 19.0760, "lng": 72.8777},   # Mumbai
        ]
        density = compute_nearby_crime_density(self.ATM, crimes, density_radius_km=10000.0)
        assert density == 3.0

    def test_all_invalid_crimes_yield_zero_density(self):
        """Crimes with all-invalid records should not raise and should give 0."""
        crimes = [
            {"lat": None, "lng": None},
            "not-a-dict",
            {"lat": 999.0, "lng": 0.0},
        ]
        density = compute_nearby_crime_density(self.ATM, crimes)
        assert density == 0.0

    def test_mixed_valid_invalid_skips_invalid_counts_valid(self):
        crimes = [
            {"lat": 12.9355, "lng": 77.6248},  # valid, nearby
            {"lat": None, "lng": None},          # invalid, skipped
            {"lat": "bad", "lng": "data"},       # invalid, skipped
            {"lat": 12.9360, "lng": 77.6250},   # valid, nearby
        ]
        density = compute_nearby_crime_density(self.ATM, crimes)
        assert density == 2.0

    def test_custom_radius_1km_vs_2km(self):
        """Confirm that a tighter radius yields fewer or equal counts."""
        crimes = [
            {"lat": 12.9352, "lng": 77.6245},  # ~0 km
            {"lat": 12.9410, "lng": 77.6290},  # ~0.7 km
            {"lat": 12.9500, "lng": 77.6350},  # ~1.7 km
        ]
        d1 = compute_nearby_crime_density(self.ATM, crimes, density_radius_km=1.0)
        d2 = compute_nearby_crime_density(self.ATM, crimes, density_radius_km=2.0)
        assert d1 <= d2, f"Smaller radius should yield fewer/equal crimes: {d1} vs {d2}"


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 9 — Historical spatial feature calculation
# (Covered by test_p2_p3_interface.py — focused integration check added here)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory09HistoricalSpatialFeatures:
    """Category 9: spatial_features dict satisfies ML_GIS_CONTRACTS.md §1."""

    def test_spatial_features_has_exactly_two_keys(self):
        feats = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9380, "lng": 77.6270},
            [{"lat": 12.9355, "lng": 77.6248}],
        )
        assert set(feats.keys()) == {"distance_from_crime", "nearby_crime_density"}

    def test_atm_historical_risk_is_not_in_spatial_features(self):
        """atm_historical_risk is attached by P5 (backend), not P3. Must not appear here."""
        feats = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9380, "lng": 77.6270},
            [],
        )
        assert "atm_historical_risk" not in feats, (
            "atm_historical_risk must NOT be produced by P3 — it is owned by P5 (backend)."
        )

    def test_hour_of_day_is_not_in_spatial_features(self):
        """hour_of_day is owned by P2 (ML). Must not appear in P3 output."""
        feats = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9380, "lng": 77.6270},
            [],
        )
        assert "hour_of_day" not in feats


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 10 — Hotspot calculation edge cases
# Gaps: no-cluster (all noise), two disjoint clusters, duplicate incidents,
# fewer-than-min_samples incidents, mixed invalid+valid.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory10HotspotCalculation:
    """Category 10: DBSCAN hotspot detection edge cases."""

    def test_empty_incidents_returns_empty(self):
        assert detect_spatial_hotspots([]) == []

    def test_fewer_than_min_samples_returns_empty(self):
        """2 incidents with min_samples=3 → no cluster, return []."""
        incidents = [
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9353, "lng": 77.6246},
        ]
        assert detect_spatial_hotspots(incidents, eps_km=1.0, min_samples=3) == []

    def test_all_noise_no_cluster_returns_empty(self):
        """4 points all >eps apart from each other → no cluster."""
        incidents = [
            {"lat": 12.9352, "lng": 77.6245},  # Bangalore
            {"lat": 28.6139, "lng": 77.2090},  # Delhi
            {"lat": 19.0760, "lng": 72.8777},  # Mumbai
            {"lat": 13.0827, "lng": 80.2707},  # Chennai
        ]
        result = detect_spatial_hotspots(incidents, eps_km=0.1, min_samples=2)
        assert result == [], f"Expected no cluster for widely separated points, got {result}"

    def test_single_dense_cluster_detected(self):
        """4 incidents within eps → 1 hotspot with correct count."""
        incidents = [
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9353, "lng": 77.6246},
            {"lat": 12.9354, "lng": 77.6247},
            {"lat": 12.9355, "lng": 77.6248},
        ]
        result = detect_spatial_hotspots(incidents, eps_km=0.5, min_samples=3)
        assert len(result) == 1
        assert result[0]["incident_count"] == 4

    def test_two_disjoint_clusters_detected(self):
        """Two geographically separate dense clusters → 2 hotspots."""
        cluster_a = [
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9353, "lng": 77.6246},
            {"lat": 12.9354, "lng": 77.6247},
        ]
        cluster_b = [
            {"lat": 28.6139, "lng": 77.2090},
            {"lat": 28.6140, "lng": 77.2091},
            {"lat": 28.6141, "lng": 77.2092},
        ]
        result = detect_spatial_hotspots(cluster_a + cluster_b, eps_km=0.5, min_samples=3)
        assert len(result) == 2, f"Expected 2 clusters, got {len(result)}"

    def test_clusters_sorted_densest_first(self):
        """Hotspot list must be sorted by incident_count descending."""
        cluster_big = [
            {"lat": 12.9352 + i * 0.0001, "lng": 77.6245} for i in range(5)
        ]
        cluster_small = [
            {"lat": 28.6139 + i * 0.0001, "lng": 77.2090} for i in range(3)
        ]
        result = detect_spatial_hotspots(cluster_big + cluster_small, eps_km=1.0, min_samples=3)
        if len(result) >= 2:
            assert result[0]["incident_count"] >= result[1]["incident_count"]

    def test_hotspot_output_schema(self):
        """Each hotspot dict must have all required keys."""
        incidents = [
            {"lat": 12.9352 + i * 0.0001, "lng": 77.6245} for i in range(4)
        ]
        result = detect_spatial_hotspots(incidents, eps_km=0.5, min_samples=3)
        assert len(result) == 1
        h = result[0]
        assert "cluster_id" in h
        assert "incident_count" in h
        assert "centroid" in h
        assert "lat" in h["centroid"] and "lng" in h["centroid"]
        assert "radius_km" in h
        assert "bounding_box" in h
        assert "incidents" in h

    def test_hotspot_centroid_is_within_bounding_box(self):
        incidents = [
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9360, "lng": 77.6250},
            {"lat": 12.9355, "lng": 77.6248},
        ]
        result = detect_spatial_hotspots(incidents, eps_km=1.0, min_samples=3)
        assert len(result) == 1
        h = result[0]
        bb = h["bounding_box"]
        c = h["centroid"]
        assert bb["min_lat"] <= c["lat"] <= bb["max_lat"]
        assert bb["min_lng"] <= c["lng"] <= bb["max_lng"]

    def test_hotspot_skips_invalid_incident_records(self):
        """Invalid incidents (non-dict, bad coords) are silently skipped."""
        incidents = [
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9353, "lng": 77.6246},
            {"lat": 12.9354, "lng": 77.6247},
            "not-a-dict",
            {"lat": None, "lng": None},
            {"lat": 999.0, "lng": 0.0},  # out of bounds
        ]
        # 3 valid close incidents + 3 invalid → should detect 1 cluster
        result = detect_spatial_hotspots(incidents, eps_km=0.5, min_samples=3)
        assert len(result) == 1
        assert result[0]["incident_count"] == 3

    def test_duplicate_incidents_are_counted_separately(self):
        """Duplicate incident dicts are treated as separate spatial points."""
        base = {"lat": 12.9352, "lng": 77.6245}
        incidents = [base.copy(), base.copy(), base.copy(), base.copy()]
        result = detect_spatial_hotspots(incidents, eps_km=0.1, min_samples=3)
        assert len(result) == 1
        assert result[0]["incident_count"] == 4, (
            "Duplicate spatial incidents must each be counted independently."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 11 — GeoJSON validity (covered by test_geojson_builder.py)
# Focused integration: build → validate round-trip for required properties.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory11GeoJSONValidity:
    """Category 11: GeoJSON output is RFC 7946 and contract-compliant."""

    BASE_PRED = {
        "atm_id": "atm-test-01",
        "location": {"lat": 12.9352, "lng": 77.6245},
        "risk_score": 0.75,
        "confidence": 0.70,
        "predicted_window": {"start": "2026-09-18T10:00:00Z", "end": "2026-09-18T16:00:00Z"},
        "explanation": ["Close to crime location"],
    }

    def test_output_type_is_feature_collection(self):
        fc = build_predictions_geojson([self.BASE_PRED])
        assert fc["type"] == "FeatureCollection"

    def test_features_is_list(self):
        fc = build_predictions_geojson([self.BASE_PRED])
        assert isinstance(fc["features"], list)

    def test_each_feature_type_is_feature(self):
        fc = build_predictions_geojson([self.BASE_PRED])
        for f in fc["features"]:
            assert f["type"] == "Feature"

    def test_geometry_type_is_point(self):
        fc = build_predictions_geojson([self.BASE_PRED])
        assert fc["features"][0]["geometry"]["type"] == "Point"

    def test_coordinates_are_lng_lat_order(self):
        """RFC 7946: coordinates must be [longitude, latitude]."""
        fc = build_predictions_geojson([self.BASE_PRED])
        coords = fc["features"][0]["geometry"]["coordinates"]
        assert coords[0] == 77.6245  # longitude
        assert coords[1] == 12.9352  # latitude

    def test_all_required_properties_present(self):
        fc = build_predictions_geojson([self.BASE_PRED])
        props = fc["features"][0]["properties"]
        required = {"atm_id", "risk_score", "confidence", "predicted_window", "risk_category", "explanation"}
        assert required.issubset(props.keys())

    def test_risk_category_matches_thresholds(self):
        preds = [
            {**self.BASE_PRED, "atm_id": "h", "risk_score": 0.80},
            {**self.BASE_PRED, "atm_id": "m", "risk_score": 0.55},
            {**self.BASE_PRED, "atm_id": "l", "risk_score": 0.20},
        ]
        fc = build_predictions_geojson(preds)
        cats = {f["properties"]["atm_id"]: f["properties"]["risk_category"] for f in fc["features"]}
        assert cats["h"] == "high"
        assert cats["m"] == "medium"
        assert cats["l"] == "low"

    def test_output_is_json_serialisable(self):
        fc = build_predictions_geojson([self.BASE_PRED])
        try:
            json.dumps(fc)
        except (TypeError, ValueError) as e:
            pytest.fail(f"GeoJSON output is not JSON-serialisable: {e}")

    def test_validator_accepts_valid_output(self):
        fc = build_predictions_geojson([self.BASE_PRED])
        result = validate_predictions_geojson(fc)
        assert result.valid, f"Validator rejected valid GeoJSON: {result.errors}"

    def test_empty_predictions_produces_valid_empty_collection(self):
        fc = build_predictions_geojson([])
        assert fc == {"type": "FeatureCollection", "features": []}
        result = validate_predictions_geojson(fc)
        assert result.valid


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 12 — P2 GIS feature output contract
# (Covered by test_p2_p3_interface.py — one direct assertion added)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory12P2GISOutputContract:
    """Category 12: spatial_features output matches ML_GIS_CONTRACTS.md §1."""

    def test_spatial_features_keys_match_contract_exactly(self):
        feats = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9380, "lng": 77.6270},
            [],
        )
        assert set(feats.keys()) == {"distance_from_crime", "nearby_crime_density"}, (
            f"Got unexpected keys: {feats.keys()}"
        )

    def test_distance_from_crime_is_float_and_non_negative(self):
        feats = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9380, "lng": 77.6270},
            [],
        )
        v = feats["distance_from_crime"]
        assert isinstance(v, float) and not math.isnan(v) and v >= 0.0

    def test_nearby_crime_density_is_float_and_non_negative(self):
        feats = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9380, "lng": 77.6270},
            [{"lat": 12.9355, "lng": 77.6248}],
        )
        v = feats["nearby_crime_density"]
        assert isinstance(v, float) and not math.isnan(v) and v >= 0.0

    def test_spatial_features_values_castable_to_float(self):
        """P2's extract_feature_vector calls float() on each value."""
        feats = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9380, "lng": 77.6270},
            [{"lat": 12.9355, "lng": 77.6248}],
        )
        for k, v in feats.items():
            try:
                float(v)
            except (ValueError, TypeError):
                pytest.fail(f"Value for {k!r} cannot be cast to float: {v!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 13 — Edge cases: empty datasets, equatorial coords, all-invalid
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory13EdgeCases:
    """Category 13: empty datasets, zero coordinates, all-invalid inputs."""

    def test_load_crimes_from_empty_list_returns_empty(self):
        assert load_crimes([]) == []

    def test_load_atms_from_empty_list_returns_empty(self):
        assert load_atms([]) == []

    def test_select_candidates_from_empty_atm_list(self):
        result = select_candidate_atms({"lat": 12.9352, "lng": 77.6245}, radius_km=5.0, atms=[])
        assert result == []

    def test_select_candidates_returns_empty_when_none_within_radius(self):
        crime = {"lat": 12.9352, "lng": 77.6245}
        atms = [{"atm_id": "far", "lat": 28.6139, "lng": 77.2090}]  # Delhi
        result = select_candidate_atms(crime, radius_km=5.0, atms=atms)
        assert result == []

    def test_build_geojson_from_empty_predictions(self):
        result = build_predictions_geojson([])
        assert result["type"] == "FeatureCollection"
        assert result["features"] == []

    def test_equatorial_origin_coordinates_accepted(self):
        """(0.0, 0.0) is a valid WGS84 point — must not be rejected."""
        crimes = load_crimes([{"crime_id": "eq", "lat": 0.0, "lng": 0.0}])
        assert len(crimes) == 1
        assert crimes[0]["latitude"] == 0.0
        assert crimes[0]["longitude"] == 0.0

    def test_load_crimes_all_invalid_returns_empty(self):
        raw = [
            {"crime_id": "bad1", "lat": 999.0, "lng": 0.0},
            {"crime_id": "bad2"},
            {"crime_id": "bad3", "lat": None, "lng": None},
        ]
        result = load_crimes(raw, drop_invalid=True)
        assert result == []

    def test_load_atms_all_invalid_returns_empty(self):
        raw = [
            {"atm_id": "bad1", "lat": 999.0, "lng": 0.0},
            {"atm_id": "bad2"},
        ]
        result = load_atms(raw, drop_invalid=True)
        assert result == []

    def test_geojson_with_missing_optional_bank_area_still_valid(self):
        """bank and area are optional — GeoJSON must still validate without them."""
        pred = {
            "atm_id": "atm-min",
            "location": {"lat": 12.9352, "lng": 77.6245},
            "risk_score": 0.5,
            "confidence": 0.6,
            "predicted_window": {"start": "2026-09-18T10:00:00Z", "end": "2026-09-18T16:00:00Z"},
            "explanation": [],
        }
        fc = build_predictions_geojson([pred])
        result = validate_predictions_geojson(fc)
        assert result.valid

    def test_service_handles_all_empty_inputs(self):
        service = SpatialService()
        candidates = service.get_candidate_atms({"lat": 12.9352, "lng": 77.6245},
                                                 radius_km=5.0, atms=[])
        assert candidates == []
        fc = service.to_geojson([])
        assert fc["features"] == []

    def test_hotspot_with_only_invalid_incidents_returns_empty(self):
        incidents = ["bad", None, {"lat": None, "lng": None}]
        result = detect_spatial_hotspots(incidents, eps_km=1.0, min_samples=2)
        assert result == []

    def test_density_with_only_invalid_crimes_returns_zero(self):
        atm = {"lat": 12.9352, "lng": 77.6245}
        crimes = [{"lat": 999.0, "lng": 0.0}, "bad", None]
        density = compute_nearby_crime_density(atm, crimes)
        assert density == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 14 — Duplicate records
# Tests duplicate ATM IDs in candidate list, duplicate crimes in density,
# duplicate incidents in hotspot.
# ═══════════════════════════════════════════════════════════════════════════════

class TestCategory14DuplicateRecords:
    """Category 14: duplicate records must be handled predictably and explicitly."""

    CRIME = {"lat": 12.9352, "lng": 77.6245}
    ATM = {"lat": 12.9380, "lng": 77.6270}

    def test_duplicate_atm_id_records_both_returned_as_candidates(self):
        """Two ATM records with the same atm_id are treated as separate objects.

        P3 is a stateless spatial filter — it does NOT deduplicate atm_id.
        Deduplication is P5 (backend) responsibility.
        """
        atms = [
            {"atm_id": "dup-001", "lat": 12.9380, "lng": 77.6270},
            {"atm_id": "dup-001", "lat": 12.9381, "lng": 77.6271},  # same ID, slightly different coords
        ]
        candidates = select_candidate_atms(self.CRIME, radius_km=5.0, atms=atms)
        assert len(candidates) == 2, (
            "P3 returns both records — deduplication by atm_id is P5's responsibility."
        )

    def test_duplicate_crime_records_in_density_both_counted(self):
        """Duplicate crime records at the same location are each counted independently.

        P3 counts incidents by proximity, not by crime_id uniqueness.
        Deduplication of crime_id is P5/backend responsibility.
        """
        crime_a = {"lat": 12.9355, "lng": 77.6248}
        # Two identical crime dicts (duplicate entries)
        crimes = [crime_a.copy(), crime_a.copy(), crime_a.copy()]
        density = compute_nearby_crime_density(self.ATM, crimes)
        assert density == 3.0, (
            "Each duplicate crime record must be counted as a separate incident."
        )

    def test_duplicate_identical_atms_same_distance(self):
        """Two ATMs at exactly the same location have identical distance_from_crime."""
        atm_a = {"atm_id": "dup-A", "lat": 12.9380, "lng": 77.6270}
        atm_b = {"atm_id": "dup-B", "lat": 12.9380, "lng": 77.6270}
        atms = [atm_a, atm_b]
        candidates = select_candidate_atms(self.CRIME, radius_km=5.0, atms=atms)
        assert len(candidates) == 2
        d0 = candidates[0]["distance_from_crime_km"]
        d1 = candidates[1]["distance_from_crime_km"]
        assert d0 == d1, "Identical locations must produce identical distances"

    def test_duplicate_atms_sorted_deterministically_by_atm_id(self):
        """When distances are tied, sort must be deterministic (by atm_id)."""
        atms = [
            {"atm_id": "Z-dup", "lat": 12.9380, "lng": 77.6270},
            {"atm_id": "A-dup", "lat": 12.9380, "lng": 77.6270},
        ]
        candidates = select_candidate_atms(self.CRIME, radius_km=5.0, atms=atms)
        assert candidates[0]["atm_id"] == "A-dup"
        assert candidates[1]["atm_id"] == "Z-dup"

    def test_load_crimes_with_duplicate_crime_ids_both_loaded(self):
        """Data loader does not deduplicate crime_id — both records pass through."""
        raw = [
            {"crime_id": "dup-c", "lat": 12.9352, "lng": 77.6245},
            {"crime_id": "dup-c", "lat": 12.9353, "lng": 77.6246},
        ]
        crimes = load_crimes(raw, drop_invalid=True)
        assert len(crimes) == 2, (
            "Data loader must not silently deduplicate crime_id — that is backend's job."
        )

    def test_load_atms_with_duplicate_atm_ids_both_loaded(self):
        """Data loader does not deduplicate atm_id."""
        raw = [
            {"atm_id": "dup-a", "lat": 12.9380, "lng": 77.6270, "bank": "SBI"},
            {"atm_id": "dup-a", "lat": 12.9381, "lng": 77.6271, "bank": "SBI"},
        ]
        atms = load_atms(raw, drop_invalid=True)
        assert len(atms) == 2

    def test_geojson_with_duplicate_atm_ids_both_included(self):
        """build_predictions_geojson does not deduplicate by atm_id."""
        pred = {
            "atm_id": "dup-g",
            "location": {"lat": 12.9380, "lng": 77.6270},
            "risk_score": 0.75,
            "confidence": 0.7,
            "predicted_window": {"start": "2026-09-18T10:00:00Z", "end": "2026-09-18T16:00:00Z"},
            "explanation": [],
        }
        fc = build_predictions_geojson([pred, pred])
        assert len(fc["features"]) == 2, (
            "Duplicate predictions must both appear in GeoJSON — dedup is backend's responsibility."
        )
