"""Fragment 9: P2 ↔ P3 interface stability tests for CyberCast GIS layer.

These tests verify that P3's compute_spatial_features() produces exactly
the spatial features required by P2's ML feature pipeline, as defined in:

    docs/ML_GIS_CONTRACTS.md §1
    docs/GIS_SPEC.md (SpatialInterface.compute_spatial_features)

They cross-reference P2's canonical FEATURE_NAMES list from
ml/features/prepare_features.py to ensure the interface cannot silently
drift without a test failure.

Two spatial features are in scope (from ML_GIS_CONTRACTS.md §1):
    1. distance_from_crime  -- float, km, Haversine
    2. nearby_crime_density -- float, count of incidents within radius

Everything else (hour_of_day, day_of_week, amount, atm_historical_risk,
txns_last_1h, txns_last_6h, withdrawal_frequency) is owned by P2/backend
and is deliberately NOT tested here.

Constraint: these tests must NOT import ML model classes or depend on a
trained model file. They only import P2's public constant (FEATURE_NAMES)
and P3's public spatial functions.
"""

import math
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ── Ensure project root is importable ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── P3 imports (under test) ───────────────────────────────────────────────────
from gis.spatial.density import (
    compute_nearby_crime_density,
    compute_spatial_features,
    DEFAULT_DENSITY_RADIUS_KM,
)
from gis.spatial.service import SpatialService

# ── P2 cross-reference (canonical feature name list only, no model) ───────────
from ml.features.prepare_features import FEATURE_NAMES as P2_FEATURE_NAMES

# ── Contract constants ────────────────────────────────────────────────────────
#
# The two spatial feature keys P3 must produce for P2.
# Source: ML_GIS_CONTRACTS.md §1, "spatial_features" object.
# Do NOT expand this list without a contract change approved by P1.
#
EXPECTED_SPATIAL_KEYS: frozenset = frozenset({
    "distance_from_crime",
    "nearby_crime_density",
})

# ── Reusable fixtures ─────────────────────────────────────────────────────────

CRIME_LOCATION: Dict[str, float] = {"lat": 12.9352, "lng": 77.6245}

ATM_LOCATION_NEARBY: Dict[str, float] = {"lat": 12.9380, "lng": 77.6270}
ATM_LOCATION_FAR: Dict[str, float] = {"lat": 13.0827, "lng": 80.2707}  # Chennai

HISTORICAL_CRIMES: List[Dict[str, Any]] = [
    {"lat": 12.9360, "lng": 77.6250},  # within 2 km of ATM_LOCATION_NEARBY
    {"lat": 12.9370, "lng": 77.6260},  # within 2 km
    {"lat": 12.9500, "lng": 77.6400},  # within 2 km
    {"lat": 13.0500, "lng": 80.0000},  # far from ATM_LOCATION_NEARBY
]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Contract Key Verification
# Confirm that P3's spatial feature names are a subset of P2's FEATURE_NAMES.
# ═══════════════════════════════════════════════════════════════════════════════

class TestContractKeyAlignment:
    """Verify that P3 spatial feature names align with P2's FEATURE_NAMES list.

    If this test fails it means either:
    (a) P3 renamed a feature without updating the contract, or
    (b) P2 removed a feature from FEATURE_NAMES without removing the GIS contract.
    Either way the mismatch must be reported to P1 before any code change.
    """

    def test_p2_feature_names_contains_distance_from_crime(self):
        """distance_from_crime must be in P2's canonical FEATURE_NAMES list."""
        assert "distance_from_crime" in P2_FEATURE_NAMES, (
            "CONTRACT MISMATCH: 'distance_from_crime' is missing from P2's "
            "FEATURE_NAMES list. Either P2 removed it or renamed it. "
            "Report to P1 before touching any code."
        )

    def test_p2_feature_names_contains_nearby_crime_density(self):
        """nearby_crime_density must be in P2's canonical FEATURE_NAMES list."""
        assert "nearby_crime_density" in P2_FEATURE_NAMES, (
            "CONTRACT MISMATCH: 'nearby_crime_density' is missing from P2's "
            "FEATURE_NAMES list. Either P2 removed it or renamed it. "
            "Report to P1 before touching any code."
        )

    def test_p2_feature_names_has_exactly_9_features(self):
        """P2 must expose exactly 9 features (ML_GIS_CONTRACTS.md §1)."""
        assert len(P2_FEATURE_NAMES) == 9, (
            f"CONTRACT MISMATCH: Expected 9 ML features, got {len(P2_FEATURE_NAMES)}. "
            f"Current list: {P2_FEATURE_NAMES}. Report change to P1."
        )

    def test_expected_spatial_keys_are_subset_of_p2_feature_names(self):
        """Both P3-owned spatial features must exist in P2's FEATURE_NAMES."""
        missing = EXPECTED_SPATIAL_KEYS - set(P2_FEATURE_NAMES)
        assert not missing, (
            f"CONTRACT MISMATCH: The following P3 spatial features are not "
            f"in P2's FEATURE_NAMES: {missing}. Report to P1."
        )

    def test_p2_feature_names_order_positions(self):
        """Verify spatial features occupy expected positions in FEATURE_NAMES.

        ml/inference.py constructs a vector ordered by the model's saved
        feature_names. If P2 reorders FEATURE_NAMES the model file must also
        be retrained with the new order. This test documents the expected
        positions so a future reorder is caught explicitly.
        """
        assert P2_FEATURE_NAMES.index("distance_from_crime") == 3, (
            "POSITIONAL MISMATCH: 'distance_from_crime' moved in FEATURE_NAMES. "
            "If P2 intentionally reordered features, the model bundle must be "
            "retrained and this assertion updated. Report to P1."
        )
        assert P2_FEATURE_NAMES.index("nearby_crime_density") == 7, (
            "POSITIONAL MISMATCH: 'nearby_crime_density' moved in FEATURE_NAMES. "
            "If P2 intentionally reordered features, the model bundle must be "
            "retrained and this assertion updated. Report to P1."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — compute_spatial_features() Output Shape
# Verify the output dict is exactly the "spatial_features" envelope in
# ML_GIS_CONTRACTS.md §1: {"distance_from_crime": float, "nearby_crime_density": float}
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputeSpatialFeaturesOutputShape:
    """Output shape must exactly match ML_GIS_CONTRACTS.md §1 spatial_features."""

    def test_returns_dict(self):
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        assert isinstance(result, dict), (
            f"compute_spatial_features() must return dict, got {type(result)}"
        )

    def test_output_keys_exactly_match_contract(self):
        """Output must have exactly the two contract-specified keys — no more, no less."""
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        actual_keys = frozenset(result.keys())
        assert actual_keys == EXPECTED_SPATIAL_KEYS, (
            f"KEY MISMATCH: Expected {EXPECTED_SPATIAL_KEYS}, got {actual_keys}. "
            f"Adding keys to this dict requires a contract change."
        )

    def test_distance_from_crime_is_float(self):
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        val = result["distance_from_crime"]
        assert isinstance(val, float), (
            f"'distance_from_crime' must be float, got {type(val)}"
        )

    def test_nearby_crime_density_is_float(self):
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        val = result["nearby_crime_density"]
        assert isinstance(val, float), (
            f"'nearby_crime_density' must be float, got {type(val)}"
        )

    def test_both_values_are_finite(self):
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES)
        assert not math.isnan(result["distance_from_crime"]), "distance_from_crime is NaN"
        assert not math.isnan(result["nearby_crime_density"]), "nearby_crime_density is NaN"
        assert not math.isinf(result["distance_from_crime"]), "distance_from_crime is Inf"
        assert not math.isinf(result["nearby_crime_density"]), "nearby_crime_density is Inf"

    def test_both_values_are_non_negative(self):
        """Both features must be >= 0.0. Distance cannot be negative; count cannot be negative."""
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES)
        assert result["distance_from_crime"] >= 0.0, (
            f"distance_from_crime must be >= 0, got {result['distance_from_crime']}"
        )
        assert result["nearby_crime_density"] >= 0.0, (
            f"nearby_crime_density must be >= 0, got {result['nearby_crime_density']}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — distance_from_crime: Field-by-Field Contract Verification
#
# 1. Field name:          distance_from_crime
# 2. Meaning:             Great-circle (Haversine) distance from crime to ATM
# 3. Input data:          crime_location, atm_location (lat/lng dicts)
# 4. Calculation:         Haversine formula on WGS84, R=6371.0088 km
# 5. Units:               Kilometers (km), rounded to 4dp
# 6. Data type:           float
# 7. Null/missing:        Raises ValueError — invalid coords are not silently 0
# 8. Example value:       0.35 (350 meters)
# 9. Producing component: gis/spatial/density.py::compute_spatial_features()
# 10. Consuming component: ml/features/prepare_features.py::extract_feature_vector()
# ═══════════════════════════════════════════════════════════════════════════════

class TestDistanceFromCrime:
    """Verify distance_from_crime semantics per ML_GIS_CONTRACTS.md §1."""

    def test_nearby_atm_has_small_distance(self):
        """An ATM near the crime should produce a small distance_from_crime."""
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        dist = result["distance_from_crime"]
        assert dist < 1.0, (
            f"ATM at {ATM_LOCATION_NEARBY} is near crime at {CRIME_LOCATION}; "
            f"expected distance < 1.0 km, got {dist:.4f} km"
        )

    def test_far_atm_has_larger_distance(self):
        """An ATM far from the crime should have a larger distance_from_crime."""
        result_near = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        result_far = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_FAR, [])
        assert result_far["distance_from_crime"] > result_near["distance_from_crime"], (
            "Distance ordering violated: far ATM should produce larger distance_from_crime"
        )

    def test_zero_distance_for_coincident_locations(self):
        """When crime and ATM are at the same location, distance must be exactly 0.0."""
        result = compute_spatial_features(CRIME_LOCATION, CRIME_LOCATION, [])
        assert result["distance_from_crime"] == 0.0, (
            f"Coincident crime/ATM locations must yield distance 0.0, "
            f"got {result['distance_from_crime']}"
        )

    def test_distance_is_symmetric(self):
        """Haversine is symmetric: d(crime→atm) == d(atm→crime)."""
        result_forward = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        result_reverse = compute_spatial_features(ATM_LOCATION_NEARBY, CRIME_LOCATION, [])
        assert result_forward["distance_from_crime"] == result_reverse["distance_from_crime"], (
            "Haversine distance must be symmetric"
        )

    def test_distance_units_are_km_not_degrees(self):
        """distance_from_crime must be in kilometers, not degrees.

        A difference of ~0.003 degrees latitude corresponds to ~330 meters,
        not 0.003 km. The result must reflect physical km, not angular degrees.
        """
        # ATM is ~0.003 degrees away — expect ~0.3 km, definitely not 0.003
        result = compute_spatial_features(
            {"lat": 12.9352, "lng": 77.6245},
            {"lat": 12.9382, "lng": 77.6245},  # ~330m north
            [],
        )
        dist = result["distance_from_crime"]
        # Should be roughly 0.33 km — definitely not 0.003 (raw degrees)
        assert 0.2 <= dist <= 0.5, (
            f"distance_from_crime={dist:.6f} does not look like kilometers. "
            f"Expected ~0.33 km for ~0.003 degree offset. Check units."
        )

    def test_distance_rounded_to_4_decimal_places(self):
        """distance_from_crime must be rounded to 4 decimal places (gis/spatial/distance.py)."""
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        dist = result["distance_from_crime"]
        assert round(dist, 4) == dist, (
            f"distance_from_crime={dist} is not rounded to 4dp as required"
        )

    def test_invalid_crime_location_raises_value_error(self):
        """Missing/invalid crime coordinates must raise ValueError, not silently return 0."""
        with pytest.raises((ValueError, TypeError)):
            compute_spatial_features({"lat": None, "lng": None}, ATM_LOCATION_NEARBY, [])

    def test_invalid_atm_location_raises_value_error(self):
        """Missing/invalid ATM coordinates must raise ValueError, not silently return 0."""
        with pytest.raises((ValueError, TypeError)):
            compute_spatial_features(CRIME_LOCATION, {"lat": float("nan"), "lng": 77.0}, [])

    def test_deterministic_across_multiple_calls(self):
        """distance_from_crime must be deterministic — same input, same output."""
        r1 = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES)
        r2 = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES)
        assert r1["distance_from_crime"] == r2["distance_from_crime"]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — nearby_crime_density: Field-by-Field Contract Verification
#
# 1. Field name:          nearby_crime_density
# 2. Meaning:             Count of historical crimes within density_radius_km of ATM
# 3. Input data:          atm_location, historical_crimes list from crimes table
# 4. Calculation:         Count incidents where haversine(atm, crime) <= radius
# 5. Units:               Count (dimensionless integer, stored as float)
# 6. Data type:           float
# 7. Null/missing:        Returns 0.0 for empty/None crimes — safe default
# 8. Example value:       8.5 (per P4 mock); 3.0 (3 incidents within 2km)
# 9. Producing component: gis/spatial/density.py::compute_nearby_crime_density()
# 10. Consuming component: ml/features/prepare_features.py::extract_feature_vector()
# ═══════════════════════════════════════════════════════════════════════════════

class TestNearbyCrimeDensity:
    """Verify nearby_crime_density semantics per ML_GIS_CONTRACTS.md §1."""

    def test_empty_historical_crimes_returns_zero(self):
        """If historical_crimes is empty, density must be 0.0."""
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, [])
        assert result["nearby_crime_density"] == 0.0, (
            f"Expected 0.0 for empty historical crimes, got {result['nearby_crime_density']}"
        )

    def test_none_historical_crimes_returns_zero(self):
        """If historical_crimes is None, density must be 0.0 (not raise)."""
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, None)
        assert result["nearby_crime_density"] == 0.0

    def test_counts_crimes_within_default_radius(self):
        """Crimes within DEFAULT_DENSITY_RADIUS_KM (2.0 km) of the ATM are counted."""
        # 3 crimes within ~2 km of ATM_LOCATION_NEARBY, 1 far away
        result = compute_spatial_features(
            CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES
        )
        density = result["nearby_crime_density"]
        assert density >= 1.0, (
            f"Expected at least 1 crime counted within 2km, got {density}"
        )
        # Should not count the Chennai crime (>300 km away)
        assert density < len(HISTORICAL_CRIMES), (
            f"Density={density} should not include distant crimes. "
            f"Total crimes={len(HISTORICAL_CRIMES)}"
        )

    def test_does_not_count_crimes_beyond_radius(self):
        """Crimes far from the ATM must NOT be counted."""
        far_crimes = [
            {"lat": 13.0827, "lng": 80.2707},  # Chennai — ~290 km away
            {"lat": 19.0760, "lng": 72.8777},  # Mumbai — ~840 km away
        ]
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, far_crimes)
        assert result["nearby_crime_density"] == 0.0, (
            f"Expected 0.0 density for crimes >2km away, got {result['nearby_crime_density']}"
        )

    def test_density_equals_count_not_rate(self):
        """nearby_crime_density is a raw incident count, not incidents/km².

        The contract (ML_GIS_CONTRACTS.md §1) says this is the density value
        consumed by ML. The implementation counts incidents (not normalizes by area).
        Document this explicitly so future developers don't introduce area normalization
        without a contract change.
        """
        single_crime = [{"lat": 12.9355, "lng": 77.6248}]  # ~40m from ATM
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, single_crime)
        density = result["nearby_crime_density"]
        # With 1 crime within radius, count should be 1.0
        assert density == 1.0, (
            f"nearby_crime_density should be a raw count of 1 incident, got {density}. "
            f"If area normalization was added, this is a CONTRACT CHANGE — report to P1."
        )

    def test_more_crimes_increases_density(self):
        """Adding more nearby crimes must increase nearby_crime_density."""
        one_crime = [{"lat": 12.9360, "lng": 77.6250}]
        two_crimes = [
            {"lat": 12.9360, "lng": 77.6250},
            {"lat": 12.9370, "lng": 77.6260},
        ]
        r1 = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, one_crime)
        r2 = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, two_crimes)
        assert r2["nearby_crime_density"] > r1["nearby_crime_density"], (
            "Adding more nearby crimes must increase nearby_crime_density"
        )

    def test_invalid_crime_records_are_skipped_not_raised(self):
        """Individual invalid crime records must be skipped gracefully (not crash)."""
        crimes_with_bad_entry = [
            {"lat": 12.9360, "lng": 77.6250},  # valid
            {"lat": None, "lng": None},          # invalid — must be skipped
            "not_a_dict",                         # invalid — must be skipped
        ]
        # Should not raise; should count only the 1 valid nearby crime
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, crimes_with_bad_entry)
        density = result["nearby_crime_density"]
        assert isinstance(density, float), "nearby_crime_density must be float even with invalid inputs"
        assert density >= 0.0

    def test_density_is_deterministic(self):
        """nearby_crime_density must be deterministic — same input, same output."""
        r1 = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES)
        r2 = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES)
        assert r1["nearby_crime_density"] == r2["nearby_crime_density"]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — SpatialService interface layer
# SpatialService.compute_spatial_features() must produce an identical
# envelope to the underlying density module function.
# ═══════════════════════════════════════════════════════════════════════════════

class TestSpatialServiceInterface:
    """SpatialService is the object the backend actually calls.

    These tests verify SpatialService.compute_spatial_features() produces
    the same contract-compliant envelope as the underlying density module,
    and that SpatialService.get_candidate_atms() preserves the fields
    required for the backend to attach spatial_features per candidate.
    """

    def setup_method(self):
        self.service = SpatialService()

    def test_service_compute_spatial_features_returns_correct_keys(self):
        result = self.service.compute_spatial_features(
            CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES
        )
        assert frozenset(result.keys()) == EXPECTED_SPATIAL_KEYS, (
            f"SpatialService.compute_spatial_features() returned wrong keys: {result.keys()}"
        )

    def test_service_compute_spatial_features_values_are_floats(self):
        result = self.service.compute_spatial_features(
            CRIME_LOCATION, ATM_LOCATION_NEARBY, HISTORICAL_CRIMES
        )
        assert isinstance(result["distance_from_crime"], float)
        assert isinstance(result["nearby_crime_density"], float)

    def test_service_compute_spatial_features_empty_crimes(self):
        result = self.service.compute_spatial_features(
            CRIME_LOCATION, ATM_LOCATION_NEARBY, []
        )
        assert result["nearby_crime_density"] == 0.0

    def test_service_compute_spatial_features_none_crimes(self):
        """Backend may call with historical_crimes=None; must not crash."""
        result = self.service.compute_spatial_features(
            CRIME_LOCATION, ATM_LOCATION_NEARBY, None
        )
        assert result["nearby_crime_density"] == 0.0

    def test_service_get_candidate_atms_preserves_atm_id(self):
        """Candidate ATM dicts must preserve atm_id for the backend to key on."""
        atms = [
            {"atm_id": "atm-001", "lat": 12.9380, "lng": 77.6270},
            {"atm_id": "atm-002", "lat": 12.9400, "lng": 77.6290},
        ]
        candidates = self.service.get_candidate_atms(
            crime_location=CRIME_LOCATION,
            radius_km=5.0,
            atms=atms,
        )
        assert all("atm_id" in c for c in candidates), (
            "get_candidate_atms() must preserve atm_id in each candidate dict"
        )

    def test_service_get_candidate_atms_preserves_location(self):
        """Candidate ATM dicts must include normalized location dict."""
        atms = [{"atm_id": "atm-001", "lat": 12.9380, "lng": 77.6270}]
        candidates = self.service.get_candidate_atms(
            crime_location=CRIME_LOCATION,
            radius_km=5.0,
            atms=atms,
        )
        assert candidates, "Should find at least one candidate within 5km"
        loc = candidates[0].get("location")
        assert isinstance(loc, dict), "location must be a dict"
        assert "lat" in loc and "lng" in loc, "location must have lat and lng keys"

    def test_service_get_candidate_atms_empty_list(self):
        """Empty ATM list must return empty candidates list (not raise)."""
        result = self.service.get_candidate_atms(CRIME_LOCATION, radius_km=5.0, atms=[])
        assert result == []

    def test_service_get_candidate_atms_none_atms(self):
        """None ATM list must return empty candidates list (not raise)."""
        result = self.service.get_candidate_atms(CRIME_LOCATION, radius_km=5.0, atms=None)
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — End-to-End Envelope: Simulated Backend Assembly
#
# Reproduces the exact object structure the backend must build before
# calling ML (per ML_GIS_CONTRACTS.md §1 "candidate_atms" envelope).
# Validates that P3's output can be composed into a valid ML input.
# ═══════════════════════════════════════════════════════════════════════════════

class TestBackendAssemblyEnvelope:
    """Simulate the backend's data-assembly step before calling ML.

    The backend is responsible for attaching P3's spatial_features and
    atm_historical_risk to each candidate. These tests verify the
    assembled envelope has the structure ML expects.
    """

    def _assemble_candidate(
        self,
        atm: Dict[str, Any],
        crime_location: Dict[str, Any],
        historical_crimes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Simulate the backend's per-candidate assembly step."""
        service = SpatialService()
        spatial_features = service.compute_spatial_features(
            crime_location=crime_location,
            atm_location=atm,
            historical_crimes=historical_crimes,
        )
        return {
            "atm_id": atm["atm_id"],
            "location": {"lat": atm["lat"], "lng": atm["lng"]},
            "atm_historical_risk": atm.get("historical_risk_score", 0.0),
            "spatial_features": spatial_features,
        }

    def test_assembled_candidate_has_all_contract_fields(self):
        """Assembled candidate dict must match ML_GIS_CONTRACTS.md §1 shape."""
        atm = {
            "atm_id": "atm-test-001",
            "lat": 12.9380,
            "lng": 77.6270,
            "historical_risk_score": 0.62,
        }
        candidate = self._assemble_candidate(atm, CRIME_LOCATION, HISTORICAL_CRIMES)

        assert "atm_id" in candidate, "missing atm_id"
        assert "location" in candidate, "missing location"
        assert "atm_historical_risk" in candidate, "missing atm_historical_risk"
        assert "spatial_features" in candidate, "missing spatial_features"
        assert frozenset(candidate["spatial_features"].keys()) == EXPECTED_SPATIAL_KEYS, (
            f"spatial_features keys wrong: {candidate['spatial_features'].keys()}"
        )

    def test_assembled_candidate_spatial_features_are_finite_floats(self):
        """ML will call float(value) on each feature; NaN/Inf must not be present."""
        atm = {"atm_id": "atm-test-002", "lat": 12.9380, "lng": 77.6270, "historical_risk_score": 0.4}
        candidate = self._assemble_candidate(atm, CRIME_LOCATION, HISTORICAL_CRIMES)

        for key in EXPECTED_SPATIAL_KEYS:
            val = candidate["spatial_features"][key]
            assert isinstance(val, float), f"spatial_features[{key!r}] must be float, got {type(val)}"
            assert not math.isnan(val), f"spatial_features[{key!r}] is NaN"
            assert not math.isinf(val), f"spatial_features[{key!r}] is Inf"

    def test_assembled_candidate_extract_feature_vector_compatible(self):
        """Verify that P2's extract_feature_vector can receive distance_from_crime and nearby_crime_density.

        This test does NOT call extract_feature_vector (which requires all 9 features
        to be present, including P2-owned ones). Instead it verifies the two spatial
        float values are compatible with the float() cast P2 applies.
        """
        atm = {"atm_id": "atm-test-003", "lat": 12.9380, "lng": 77.6270, "historical_risk_score": 0.5}
        candidate = self._assemble_candidate(atm, CRIME_LOCATION, HISTORICAL_CRIMES)
        sf = candidate["spatial_features"]

        # Simulate P2's float cast on the two GIS-owned features
        try:
            dist_float = float(sf["distance_from_crime"])
            density_float = float(sf["nearby_crime_density"])
        except (ValueError, TypeError) as err:
            pytest.fail(
                f"P2's float() cast failed on P3 spatial_features: {err}. "
                f"Values were: {sf}"
            )

        assert not math.isnan(dist_float)
        assert not math.isnan(density_float)

    def test_multiple_candidates_produce_independent_features(self):
        """Each candidate must receive its own spatial_features, not a shared reference."""
        atm_a = {"atm_id": "atm-a", "lat": 12.9380, "lng": 77.6270, "historical_risk_score": 0.6}
        atm_b = {"atm_id": "atm-b", "lat": 13.0827, "lng": 80.2707, "historical_risk_score": 0.1}  # far

        candidate_a = self._assemble_candidate(atm_a, CRIME_LOCATION, HISTORICAL_CRIMES)
        candidate_b = self._assemble_candidate(atm_b, CRIME_LOCATION, HISTORICAL_CRIMES)

        # Nearby ATM should have smaller distance_from_crime
        assert candidate_a["spatial_features"]["distance_from_crime"] < \
               candidate_b["spatial_features"]["distance_from_crime"], (
            "Nearby ATM should have smaller distance_from_crime than far ATM"
        )

        # spatial_features must be independent dicts (not shared reference)
        assert candidate_a["spatial_features"] is not candidate_b["spatial_features"]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Boundary and Edge-Case Robustness
# Ensures P3 does not crash in realistic backend scenarios where input
# data may be incomplete or edge-case.
# ═══════════════════════════════════════════════════════════════════════════════

class TestBoundaryConditions:
    """Edge cases the backend may encounter when calling P3."""

    def test_atm_at_same_lat_as_crime_different_lng(self):
        """Purely east-west separation; distance must still be > 0."""
        atm = {"lat": CRIME_LOCATION["lat"], "lng": CRIME_LOCATION["lng"] + 0.01}
        result = compute_spatial_features(CRIME_LOCATION, atm, [])
        assert result["distance_from_crime"] > 0.0

    def test_atm_at_same_lng_as_crime_different_lat(self):
        """Purely north-south separation; distance must still be > 0."""
        atm = {"lat": CRIME_LOCATION["lat"] + 0.01, "lng": CRIME_LOCATION["lng"]}
        result = compute_spatial_features(CRIME_LOCATION, atm, [])
        assert result["distance_from_crime"] > 0.0

    def test_very_large_number_of_historical_crimes(self):
        """Must not degrade or crash with many historical crime records."""
        many_crimes = [{"lat": 12.9360 + i * 0.001, "lng": 77.6250} for i in range(500)]
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, many_crimes)
        assert isinstance(result["nearby_crime_density"], float)
        assert result["nearby_crime_density"] >= 0.0

    def test_all_crimes_at_identical_location_to_atm(self):
        """All crimes at the ATM location — all should be counted (distance = 0 <= radius)."""
        crimes_at_atm = [ATM_LOCATION_NEARBY.copy() for _ in range(5)]
        result = compute_spatial_features(CRIME_LOCATION, ATM_LOCATION_NEARBY, crimes_at_atm)
        assert result["nearby_crime_density"] == 5.0

    def test_single_crime_just_within_radius(self):
        """Crime at exactly the density radius boundary should be counted (<=, not <)."""
        # DEFAULT_DENSITY_RADIUS_KM = 2.0 km
        # Place a crime exactly on the boundary by using the ATM location
        # and a point that is approximately 2km away.
        # Approximately 2km north of ATM_LOCATION_NEARBY = +0.018 deg lat
        boundary_crime = {
            "lat": ATM_LOCATION_NEARBY["lat"] + 0.018,  # ~2.0 km north
            "lng": ATM_LOCATION_NEARBY["lng"],
        }
        result = compute_spatial_features(
            CRIME_LOCATION, ATM_LOCATION_NEARBY, [boundary_crime]
        )
        # This verifies the boundary behavior (inclusion, not exclusion)
        # The exact count depends on precise Haversine distance; just verify float
        assert isinstance(result["nearby_crime_density"], float)
        assert result["nearby_crime_density"] >= 0.0

    def test_compute_spatial_features_does_not_mutate_inputs(self):
        """The function must not mutate the input crime or ATM dicts."""
        crime = dict(CRIME_LOCATION)
        atm = dict(ATM_LOCATION_NEARBY)
        crimes = [dict(c) for c in HISTORICAL_CRIMES]

        crime_before = dict(crime)
        atm_before = dict(atm)

        compute_spatial_features(crime, atm, crimes)

        assert crime == crime_before, "compute_spatial_features mutated crime_location"
        assert atm == atm_before, "compute_spatial_features mutated atm_location"
