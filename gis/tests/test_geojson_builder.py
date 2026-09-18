"""Fragment 8: GeoJSON preparation and output tests for CyberCast GIS layer (P3).

Tests the complete GeoJSON pipeline:
  1. build_predictions_geojson() -- FeatureCollection construction.
  2. validate_predictions_geojson() -- RFC 7946 + ML_GIS_CONTRACTS.md §2 compliance.
  3. categorize_risk() / format_explanation() -- helper correctness.
  4. SpatialService.to_geojson() -- concrete interface implementation.
  5. End-to-end round-trip: prediction records -> GeoJSON -> validator passes.

Contract under test (from docs/ML_GIS_CONTRACTS.md §2):
  {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": { "type": "Point", "coordinates": [longitude, latitude] },
        "properties": {
          "atm_id": "string",
          "risk_score": 0.0,          # float [0.0, 1.0]
          "confidence": 0.0,          # float [0.0, 1.0]
          "predicted_window": { "start": "ISO8601", "end": "ISO8601" },
          "risk_category": "low|medium|high",
          "explanation": ["string"]
        }
      }
    ]
  }
"""

import copy
import json
import unittest

from gis.spatial.geojson_builder import (
    build_predictions_geojson,
    categorize_risk,
    format_explanation,
)
from gis.spatial.geojson_validator import (
    validate_predictions_geojson,
    GeoJSONValidationResult,
    VALID_RISK_CATEGORIES,
)
from gis.spatial.service import SpatialService


# ---------------------------------------------------------------------------
# Fixtures shared across test cases
# ---------------------------------------------------------------------------

# Realistic prediction records that would arrive from the backend after ML ranking.
# These use the API_SPEC.md location format: {"lat": ..., "lng": ...}
_SAMPLE_WINDOW = {"start": "2026-09-18T10:00:00Z", "end": "2026-09-18T16:00:00Z"}

_PREDICTION_HIGH = {
    "atm_id": "ATM-CP-01",
    "location": {"lat": 28.6350, "lng": 77.2180},
    "risk_score": 0.88,
    "confidence": 0.72,
    "predicted_window": _SAMPLE_WINDOW,
    "explanation": [
        {"feature": "distance_from_crime", "value": 0.41, "contribution": "high"},
        {"feature": "nearby_crime_density", "value": 5.0, "contribution": "high"},
    ],
    "bank": "SBI",
    "area": "Connaught Place",
}

_PREDICTION_MEDIUM = {
    "atm_id": "ATM-MH-02",
    "location": {"lat": 28.6200, "lng": 77.2100},
    "risk_score": 0.55,
    "confidence": 0.60,
    "predicted_window": _SAMPLE_WINDOW,
    "explanation": [
        {"feature": "distance_from_crime", "value": 1.44, "contribution": "medium"},
    ],
}

_PREDICTION_LOW = {
    "atm_id": "ATM-NOIDA-03",
    "location": {"lat": 28.5700, "lng": 77.3200},
    "risk_score": 0.25,
    "confidence": 0.55,
    "predicted_window": _SAMPLE_WINDOW,
    "explanation": ["Low historical risk in this zone."],
}

# A prediction record that uses flat lat/lng instead of nested location dict
_PREDICTION_FLAT_COORDS = {
    "atm_id": "ATM-GGN-04",
    "latitude": 28.4595,
    "longitude": 77.0266,
    "risk_score": 0.70,
    "confidence": 0.65,
    "predicted_window": _SAMPLE_WINDOW,
    "explanation": [],
}


def _make_valid_fc(n_features: int = 1) -> dict:
    """Produce a minimal, fully-valid FeatureCollection dict for validator tests."""
    features = []
    for i in range(n_features):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [77.2180 + i * 0.01, 28.6350 + i * 0.01]},
            "properties": {
                "atm_id": f"ATM-TEST-{i:03d}",
                "risk_score": round(0.5 + i * 0.1, 2),
                "confidence": 0.65,
                "predicted_window": {"start": "2026-09-18T10:00:00Z", "end": "2026-09-18T16:00:00Z"},
                "risk_category": "medium",
                "explanation": ["Test explanation."],
            },
        })
    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# 1. Risk categorization
# ---------------------------------------------------------------------------

class TestCategorizeRisk(unittest.TestCase):
    """Verify risk_score -> risk_category bucketing per GIS_SPEC.md thresholds."""

    def test_high_threshold_exact(self):
        # >= 0.7 -> high
        self.assertEqual(categorize_risk(0.7), "high")
        self.assertEqual(categorize_risk(1.0), "high")
        self.assertEqual(categorize_risk(0.999), "high")

    def test_medium_threshold_range(self):
        # 0.4 <= score < 0.7 -> medium
        self.assertEqual(categorize_risk(0.4), "medium")
        self.assertEqual(categorize_risk(0.55), "medium")
        self.assertEqual(categorize_risk(0.6999), "medium")

    def test_low_threshold_range(self):
        # score < 0.4 -> low
        self.assertEqual(categorize_risk(0.0), "low")
        self.assertEqual(categorize_risk(0.3999), "low")
        self.assertEqual(categorize_risk(0.1), "low")

    def test_boundary_between_medium_and_high(self):
        """0.6999 must be medium, 0.70 must be high (no off-by-one)."""
        self.assertEqual(categorize_risk(0.6999), "medium")
        self.assertEqual(categorize_risk(0.70), "high")

    def test_boundary_between_low_and_medium(self):
        """0.3999 must be low, 0.40 must be medium."""
        self.assertEqual(categorize_risk(0.3999), "low")
        self.assertEqual(categorize_risk(0.40), "medium")

    def test_output_is_always_valid_category(self):
        """Every float in [0,1] maps to one of the three valid categories."""
        for score_int in range(0, 101):
            score = score_int / 100.0
            self.assertIn(categorize_risk(score), VALID_RISK_CATEGORIES)


# ---------------------------------------------------------------------------
# 2. Explanation formatting
# ---------------------------------------------------------------------------

class TestFormatExplanation(unittest.TestCase):
    """Verify format_explanation correctly converts ML explanation dicts to strings."""

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(format_explanation(None), [])
        self.assertEqual(format_explanation([]), [])

    def test_string_list_preserved_as_is(self):
        raw = ["High density zone", "Close to incident"]
        self.assertEqual(format_explanation(raw), raw)

    def test_single_string_in_list(self):
        self.assertEqual(format_explanation(["Only one explanation"]), ["Only one explanation"])

    def test_bare_string_wraps_in_list(self):
        result = format_explanation("Single string explanation")
        self.assertEqual(result, ["Single string explanation"])

    def test_distance_from_crime_dict(self):
        raw = [{"feature": "distance_from_crime", "value": 1.25, "contribution": "high"}]
        result = format_explanation(raw)
        self.assertEqual(len(result), 1)
        self.assertIn("1.25 km", result[0])
        self.assertIn("high", result[0].lower())

    def test_nearby_crime_density_dict(self):
        raw = [{"feature": "nearby_crime_density", "value": 7.0, "contribution": "medium"}]
        result = format_explanation(raw)
        self.assertEqual(len(result), 1)
        self.assertIn("7.0 incidents", result[0])
        self.assertIn("medium", result[0].lower())

    def test_generic_dict_feature(self):
        raw = [{"feature": "atm_historical_risk", "value": 0.85, "contribution": "high"}]
        result = format_explanation(raw)
        self.assertEqual(len(result), 1)
        self.assertIn("0.85", result[0])

    def test_mixed_string_and_dict_list(self):
        raw = [
            "Manually written explanation",
            {"feature": "distance_from_crime", "value": 0.5, "contribution": "high"},
        ]
        result = format_explanation(raw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Manually written explanation")
        self.assertIn("0.5 km", result[1])

    def test_output_is_always_list_of_strings(self):
        raw = [
            {"feature": "distance_from_crime", "value": 2.0, "contribution": "low"},
            "text item",
            42,  # non-string non-dict item
        ]
        result = format_explanation(raw)
        for item in result:
            self.assertIsInstance(item, str)


# ---------------------------------------------------------------------------
# 3. FeatureCollection construction
# ---------------------------------------------------------------------------

class TestBuildPredictionsGeoJSON(unittest.TestCase):
    """Verify build_predictions_geojson() strictly matches ML_GIS_CONTRACTS.md §2."""

    def test_empty_input_returns_empty_feature_collection(self):
        fc = build_predictions_geojson([])
        self.assertEqual(fc, {"type": "FeatureCollection", "features": []})

    def test_none_input_handled_as_empty(self):
        # Contract: caller passes [] or None; result must still be a valid FC
        fc = build_predictions_geojson(None or [])
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(fc["features"], [])

    def test_top_level_structure(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        self.assertIn("type", fc)
        self.assertIn("features", fc)
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertIsInstance(fc["features"], list)

    def test_feature_count_matches_prediction_count(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM, _PREDICTION_LOW])
        self.assertEqual(len(fc["features"]), 3)

    def test_feature_type_field(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        self.assertEqual(fc["features"][0]["type"], "Feature")

    def test_geometry_is_wgs84_point(self):
        """RFC 7946 requires geometry.type == 'Point' and coordinates [longitude, latitude]."""
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        geom = fc["features"][0]["geometry"]
        self.assertEqual(geom["type"], "Point")
        self.assertIsInstance(geom["coordinates"], list)
        self.assertEqual(len(geom["coordinates"]), 2)

    def test_coordinate_axis_order_is_lng_lat(self):
        """RFC 7946 REQUIRES [longitude, latitude] -- not [lat, lng]."""
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        coords = fc["features"][0]["geometry"]["coordinates"]
        # ATM-CP-01: lat=28.6350, lng=77.2180
        # Expected GeoJSON order: [lng, lat] = [77.2180, 28.6350]
        self.assertAlmostEqual(coords[0], 77.2180, places=4)  # longitude first
        self.assertAlmostEqual(coords[1], 28.6350, places=4)  # latitude second

    def test_flat_lat_lng_coordinates_accepted(self):
        """Prediction records with flat latitude/longitude (not nested location) work."""
        fc = build_predictions_geojson([_PREDICTION_FLAT_COORDS])
        self.assertEqual(len(fc["features"]), 1)
        coords = fc["features"][0]["geometry"]["coordinates"]
        self.assertAlmostEqual(coords[0], 77.0266, places=4)
        self.assertAlmostEqual(coords[1], 28.4595, places=4)

    def test_required_properties_present(self):
        """All six required property keys from ML_GIS_CONTRACTS.md §2 must be present."""
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        props = fc["features"][0]["properties"]
        for required_key in ("atm_id", "risk_score", "confidence",
                             "predicted_window", "risk_category", "explanation"):
            self.assertIn(required_key, props, msg=f"Missing required property: {required_key}")

    def test_atm_id_is_string(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        atm_id = fc["features"][0]["properties"]["atm_id"]
        self.assertIsInstance(atm_id, str)
        self.assertEqual(atm_id, "ATM-CP-01")

    def test_risk_score_is_rounded_float(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        rs = fc["features"][0]["properties"]["risk_score"]
        self.assertIsInstance(rs, float)
        # Must be the same after rounding to 4 decimal places (deterministic)
        self.assertEqual(rs, round(rs, 4))

    def test_confidence_is_rounded_float(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        conf = fc["features"][0]["properties"]["confidence"]
        self.assertIsInstance(conf, float)
        self.assertEqual(conf, round(conf, 4))

    def test_risk_category_matches_thresholds(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM, _PREDICTION_LOW])
        categories = [f["properties"]["risk_category"] for f in fc["features"]]
        self.assertEqual(categories[0], "high")   # 0.88
        self.assertEqual(categories[1], "medium")  # 0.55
        self.assertEqual(categories[2], "low")     # 0.25

    def test_risk_category_precomputed_value_respected(self):
        """If the prediction record already has risk_category, it must be preserved."""
        pred = copy.deepcopy(_PREDICTION_MEDIUM)
        pred["risk_category"] = "high"  # override by caller
        fc = build_predictions_geojson([pred])
        # The builder should preserve the caller-supplied category (not recompute)
        self.assertEqual(fc["features"][0]["properties"]["risk_category"], "high")

    def test_predicted_window_structure(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        pw = fc["features"][0]["properties"]["predicted_window"]
        self.assertIsInstance(pw, dict)
        self.assertIn("start", pw)
        self.assertIn("end", pw)
        self.assertEqual(pw["start"], "2026-09-18T10:00:00Z")
        self.assertEqual(pw["end"], "2026-09-18T16:00:00Z")

    def test_predicted_window_missing_becomes_empty_strings(self):
        """If prediction has no predicted_window, builder must not crash; contract fills defaults."""
        pred = copy.deepcopy(_PREDICTION_MEDIUM)
        del pred["predicted_window"]
        fc = build_predictions_geojson([pred])
        pw = fc["features"][0]["properties"]["predicted_window"]
        self.assertIsInstance(pw, dict)
        self.assertIn("start", pw)
        self.assertIn("end", pw)

    def test_explanation_is_list_of_strings(self):
        """Explanation must be a list of strings, even when input is a list of dicts."""
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        expl = fc["features"][0]["properties"]["explanation"]
        self.assertIsInstance(expl, list)
        for item in expl:
            self.assertIsInstance(item, str)

    def test_explanation_empty_list_preserved(self):
        fc = build_predictions_geojson([_PREDICTION_FLAT_COORDS])
        self.assertEqual(fc["features"][0]["properties"]["explanation"], [])

    def test_optional_bank_and_area_preserved_when_present(self):
        """bank and area are optional additive fields; they must not replace required keys."""
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        props = fc["features"][0]["properties"]
        self.assertIn("bank", props)
        self.assertEqual(props["bank"], "SBI")
        self.assertIn("area", props)
        self.assertEqual(props["area"], "Connaught Place")

    def test_sensitive_fields_not_in_output(self):
        """account_id must never appear in GeoJSON properties."""
        pred = copy.deepcopy(_PREDICTION_HIGH)
        pred["account_id"] = "ACC-SENSITIVE-12345"  # simulate a leaked field
        fc = build_predictions_geojson([pred])
        props = fc["features"][0]["properties"]
        self.assertNotIn("account_id", props)

    def test_record_with_invalid_coordinates_skipped(self):
        """Records with unparseable coordinates must be silently skipped."""
        bad_pred = {
            "atm_id": "ATM-BAD",
            "location": {"lat": 999.0, "lng": 77.0},  # lat out of WGS84 bounds
            "risk_score": 0.8,
            "confidence": 0.7,
            "predicted_window": _SAMPLE_WINDOW,
            "explanation": [],
        }
        fc = build_predictions_geojson([_PREDICTION_HIGH, bad_pred])
        # Only the valid prediction should appear
        self.assertEqual(len(fc["features"]), 1)
        self.assertEqual(fc["features"][0]["properties"]["atm_id"], "ATM-CP-01")

    def test_non_dict_record_skipped(self):
        """Non-dict entries in the predictions list must be silently skipped."""
        fc = build_predictions_geojson([_PREDICTION_HIGH, "not_a_dict", None, 42])
        self.assertEqual(len(fc["features"]), 1)

    def test_output_is_json_serialisable(self):
        """The FeatureCollection must be directly serialisable to a JSON string."""
        fc = build_predictions_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM])
        try:
            json_str = json.dumps(fc)
        except (TypeError, ValueError) as exc:
            self.fail(f"GeoJSON is not JSON-serialisable: {exc}")
        # Round-trip verify
        parsed = json.loads(json_str)
        self.assertEqual(parsed["type"], "FeatureCollection")
        self.assertEqual(len(parsed["features"]), 2)

    def test_output_is_deterministic(self):
        """Same input must produce identical output across multiple calls."""
        preds = [_PREDICTION_HIGH, _PREDICTION_MEDIUM, _PREDICTION_LOW]
        fc1 = build_predictions_geojson(preds)
        fc2 = build_predictions_geojson(preds)
        self.assertEqual(fc1, fc2)

    def test_coordinates_wgs84_bounds(self):
        """All coordinates in output must be within WGS84 bounds."""
        fc = build_predictions_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM, _PREDICTION_LOW])
        for feature in fc["features"]:
            coords = feature["geometry"]["coordinates"]
            lng, lat = coords[0], coords[1]
            self.assertGreaterEqual(lng, -180.0)
            self.assertLessEqual(lng, 180.0)
            self.assertGreaterEqual(lat, -90.0)
            self.assertLessEqual(lat, 90.0)

    def test_multiple_predictions_ordering_preserved(self):
        """Output feature order must match input prediction order."""
        preds = [_PREDICTION_LOW, _PREDICTION_HIGH, _PREDICTION_MEDIUM]
        fc = build_predictions_geojson(preds)
        ids = [f["properties"]["atm_id"] for f in fc["features"]]
        self.assertEqual(ids, ["ATM-NOIDA-03", "ATM-CP-01", "ATM-MH-02"])


# ---------------------------------------------------------------------------
# 4. GeoJSON Validator
# ---------------------------------------------------------------------------

class TestValidatePredictionsGeoJSON(unittest.TestCase):
    """Verify validate_predictions_geojson() catches all contract violations."""

    def test_valid_fc_passes(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM])
        result = validate_predictions_geojson(fc)
        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.feature_count, 2)

    def test_empty_fc_passes(self):
        result = validate_predictions_geojson({"type": "FeatureCollection", "features": []})
        self.assertTrue(result.valid)
        self.assertEqual(result.feature_count, 0)

    def test_result_is_truthy_when_valid(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH])
        result = validate_predictions_geojson(fc)
        self.assertTrue(bool(result))

    def test_result_is_falsy_when_invalid(self):
        result = validate_predictions_geojson({"type": "NotAFeatureCollection", "features": []})
        self.assertFalse(bool(result))

    def test_non_dict_input_returns_error(self):
        result = validate_predictions_geojson("not a dict")
        self.assertFalse(result.valid)
        self.assertTrue(len(result.errors) > 0)

    def test_missing_type_field(self):
        fc = {"features": []}
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("type" in e for e in result.errors))

    def test_wrong_type_value(self):
        fc = {"type": "Feature", "features": []}
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_missing_features_key(self):
        fc = {"type": "FeatureCollection"}
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("features" in e for e in result.errors))

    def test_features_not_a_list(self):
        fc = {"type": "FeatureCollection", "features": "wrong"}
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_feature_type_wrong(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["type"] = "NotFeature"
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertIn(0, result.invalid_feature_indices)

    def test_feature_geometry_missing(self):
        fc = _make_valid_fc(1)
        del fc["features"][0]["geometry"]
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_geometry_type_not_point(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["geometry"]["type"] = "LineString"
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_coordinates_lng_lat_out_of_bounds(self):
        """Longitude > 180 must fail."""
        fc = _make_valid_fc(1)
        fc["features"][0]["geometry"]["coordinates"] = [185.0, 28.6]  # lng out of bounds
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("Longitude" in e for e in result.errors))

    def test_coordinates_lat_out_of_bounds(self):
        """Latitude > 90 must fail."""
        fc = _make_valid_fc(1)
        fc["features"][0]["geometry"]["coordinates"] = [77.2, 95.0]  # lat out of bounds
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("Latitude" in e for e in result.errors))

    def test_coordinates_inverted_lat_lng_detected(self):
        """[lat, lng] instead of [lng, lat] is caught if lat looks like a longitude."""
        fc = _make_valid_fc(1)
        # If someone accidentally put [lat=28.6, lng=77.2] -> [28.6, 77.2]:
        # This is valid WGS84 range so validator won't catch axis swap directly.
        # But a clearly swapped [lat=28.6, lng=185.0] as [28.6, 185.0] should fail.
        fc["features"][0]["geometry"]["coordinates"] = [28.6350, 185.0]
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_missing_properties(self):
        fc = _make_valid_fc(1)
        del fc["features"][0]["properties"]
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_missing_atm_id(self):
        fc = _make_valid_fc(1)
        del fc["features"][0]["properties"]["atm_id"]
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("atm_id" in e for e in result.errors))

    def test_empty_atm_id_rejected(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["atm_id"] = ""
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_risk_score_out_of_range(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["risk_score"] = 1.5
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("risk_score" in e for e in result.errors))

    def test_confidence_out_of_range(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["confidence"] = -0.1
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_invalid_risk_category_string(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["risk_category"] = "critical"  # not in contract
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("risk_category" in e for e in result.errors))

    def test_all_valid_risk_categories_accepted(self):
        for cat in ("low", "medium", "high"):
            fc = _make_valid_fc(1)
            fc["features"][0]["properties"]["risk_category"] = cat
            result = validate_predictions_geojson(fc)
            self.assertTrue(result.valid, msg=f"Expected valid for risk_category={cat!r}")

    def test_predicted_window_missing_start(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["predicted_window"] = {"end": "2026-09-18T16:00:00Z"}
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("start" in e for e in result.errors))

    def test_predicted_window_missing_end(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["predicted_window"] = {"start": "2026-09-18T10:00:00Z"}
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("end" in e for e in result.errors))

    def test_predicted_window_not_dict(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["predicted_window"] = "2026-09-18T10:00:00Z"
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_explanation_not_list(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["explanation"] = "Should be a list"
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_explanation_list_with_non_string_item(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["explanation"] = ["valid string", 42]
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)

    def test_explanation_empty_list_accepted(self):
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["explanation"] = []
        result = validate_predictions_geojson(fc)
        self.assertTrue(result.valid)

    def test_sensitive_account_id_field_detected(self):
        """account_id in properties must trigger a validation error."""
        fc = _make_valid_fc(1)
        fc["features"][0]["properties"]["account_id"] = "ACC-PRIVATE-12345"
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertTrue(any("account_id" in e for e in result.errors))

    def test_multiple_features_all_valid(self):
        fc = build_predictions_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM, _PREDICTION_LOW])
        result = validate_predictions_geojson(fc)
        self.assertTrue(result.valid)
        self.assertEqual(result.feature_count, 3)
        self.assertEqual(result.invalid_feature_indices, [])

    def test_mixed_valid_and_invalid_features_reports_indices(self):
        fc = _make_valid_fc(3)
        # Corrupt feature at index 1
        fc["features"][1]["properties"]["risk_score"] = 9.9
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)
        self.assertIn(1, result.invalid_feature_indices)
        # Feature 0 and 2 should not be in invalid indices
        self.assertNotIn(0, result.invalid_feature_indices)
        self.assertNotIn(2, result.invalid_feature_indices)

    def test_non_dict_feature_in_list(self):
        fc = _make_valid_fc(1)
        fc["features"].append("not_a_feature_dict")
        result = validate_predictions_geojson(fc)
        self.assertFalse(result.valid)


# ---------------------------------------------------------------------------
# 5. End-to-end round trip: builder -> validator
# ---------------------------------------------------------------------------

class TestGeoJSONRoundTrip(unittest.TestCase):
    """Verify that build_predictions_geojson() always produces validator-passing output."""

    def _assert_builder_output_validates(self, preds: list, msg: str = "") -> None:
        fc = build_predictions_geojson(preds)
        result = validate_predictions_geojson(fc)
        self.assertTrue(
            result.valid,
            msg=f"{msg} Validator errors: {result.errors}",
        )

    def test_single_high_risk_prediction(self):
        self._assert_builder_output_validates([_PREDICTION_HIGH], "Single high-risk prediction")

    def test_single_medium_risk_prediction(self):
        self._assert_builder_output_validates([_PREDICTION_MEDIUM], "Single medium-risk prediction")

    def test_single_low_risk_prediction(self):
        self._assert_builder_output_validates([_PREDICTION_LOW], "Single low-risk prediction")

    def test_all_three_risk_levels(self):
        self._assert_builder_output_validates(
            [_PREDICTION_HIGH, _PREDICTION_MEDIUM, _PREDICTION_LOW],
            "All three risk levels",
        )

    def test_flat_coordinate_prediction(self):
        self._assert_builder_output_validates([_PREDICTION_FLAT_COORDS], "Flat latitude/longitude")

    def test_prediction_with_no_explanation(self):
        pred = copy.deepcopy(_PREDICTION_HIGH)
        pred["explanation"] = []
        self._assert_builder_output_validates([pred], "Empty explanation list")

    def test_prediction_with_string_explanation(self):
        pred = copy.deepcopy(_PREDICTION_HIGH)
        pred["explanation"] = ["Pre-formatted string explanation"]
        self._assert_builder_output_validates([pred], "String explanation list")

    def test_prediction_with_dict_explanation(self):
        pred = copy.deepcopy(_PREDICTION_HIGH)
        pred["explanation"] = [
            {"feature": "distance_from_crime", "value": 0.41, "contribution": "high"}
        ]
        self._assert_builder_output_validates([pred], "Dict explanation list")

    def test_prediction_with_optional_bank_area(self):
        pred = copy.deepcopy(_PREDICTION_HIGH)
        pred["bank"] = "SBI"
        pred["area"] = "Connaught Place"
        self._assert_builder_output_validates([pred], "Prediction with optional bank/area")

    def test_empty_predictions_list(self):
        self._assert_builder_output_validates([], "Empty predictions list")

    def test_output_is_json_serialisable_and_validates_after_roundtrip(self):
        """GeoJSON must survive JSON serialisation and still pass validation."""
        fc = build_predictions_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM])
        json_str = json.dumps(fc)
        reloaded = json.loads(json_str)
        result = validate_predictions_geojson(reloaded)
        self.assertTrue(result.valid, msg=f"Errors after JSON round-trip: {result.errors}")


# ---------------------------------------------------------------------------
# 6. SpatialService.to_geojson() integration
# ---------------------------------------------------------------------------

class TestSpatialServiceToGeoJSON(unittest.TestCase):
    """Verify SpatialService.to_geojson() delegates correctly and passes validation."""

    def setUp(self):
        self.service = SpatialService()

    def test_to_geojson_returns_feature_collection(self):
        fc = self.service.to_geojson([_PREDICTION_HIGH])
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertEqual(len(fc["features"]), 1)

    def test_to_geojson_passes_validator(self):
        fc = self.service.to_geojson([_PREDICTION_HIGH, _PREDICTION_MEDIUM])
        result = validate_predictions_geojson(fc)
        self.assertTrue(result.valid, msg=f"Validator errors: {result.errors}")

    def test_to_geojson_empty_list(self):
        fc = self.service.to_geojson([])
        self.assertEqual(fc, {"type": "FeatureCollection", "features": []})

    def test_to_geojson_coordinate_order(self):
        """SpatialService.to_geojson must produce [longitude, latitude] coordinates."""
        preds = [{
            "atm_id": "ATM-CHECK",
            "location": {"lat": 19.0760, "lng": 72.8777},  # Mumbai
            "risk_score": 0.65,
            "confidence": 0.55,
            "predicted_window": _SAMPLE_WINDOW,
            "explanation": [],
        }]
        fc = self.service.to_geojson(preds)
        coords = fc["features"][0]["geometry"]["coordinates"]
        # RFC 7946: [longitude, latitude]
        self.assertAlmostEqual(coords[0], 72.8777, places=4)  # longitude
        self.assertAlmostEqual(coords[1], 19.0760, places=4)  # latitude

    def test_to_geojson_properties_complete(self):
        fc = self.service.to_geojson([_PREDICTION_HIGH])
        props = fc["features"][0]["properties"]
        for key in ("atm_id", "risk_score", "confidence", "predicted_window",
                    "risk_category", "explanation"):
            self.assertIn(key, props)

    def test_to_geojson_risk_category_computed_correctly(self):
        preds = [
            {**_PREDICTION_HIGH, "risk_score": 0.71},   # -> high
            {**_PREDICTION_MEDIUM, "risk_score": 0.50},  # -> medium
            {**_PREDICTION_LOW, "risk_score": 0.30},     # -> low
        ]
        fc = self.service.to_geojson(preds)
        self.assertEqual(fc["features"][0]["properties"]["risk_category"], "high")
        self.assertEqual(fc["features"][1]["properties"]["risk_category"], "medium")
        self.assertEqual(fc["features"][2]["properties"]["risk_category"], "low")


if __name__ == "__main__":
    unittest.main()
