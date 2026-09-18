"""GeoJSON FeatureCollection validator for CyberCast GIS layer (P3).

Validates that a GeoJSON FeatureCollection produced by build_predictions_geojson()
strictly conforms to:
  - RFC 7946 structural requirements (type, features, geometry, properties).
  - ML_GIS_CONTRACTS.md §2 required property fields and value constraints.
  - WGS84 / EPSG:4326 coordinate range requirements.
  - [longitude, latitude] axis order as mandated by RFC 7946.

This module is pure validation -- it never modifies input, never queries the database,
and has no side effects. The backend (P5) may call it as a pre-flight sanity check
before serving the FeatureCollection to P4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class GeoJSONValidationResult:
    """Result of a GeoJSON FeatureCollection validation run.

    Attributes:
        valid: True if the FeatureCollection is fully compliant with the contract.
        errors: List of human-readable error strings describing contract violations.
        warnings: Non-fatal observations.
        feature_count: Total features inspected.
        invalid_feature_indices: Indices of Feature objects that failed validation.
    """

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    feature_count: int = 0
    invalid_feature_indices: List[int] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


# ---------------------------------------------------------------------------
# Contract constants (mirrors GIS_SPEC.md and ML_GIS_CONTRACTS.md §2)
# ---------------------------------------------------------------------------

VALID_RISK_CATEGORIES = frozenset({"low", "medium", "high"})

# RFC 7946 WGS84 bounds: longitude in [-180, 180], latitude in [-90, 90]
_LNG_MIN, _LNG_MAX = -180.0, 180.0
_LAT_MIN, _LAT_MAX = -90.0, 90.0

# Required keys at each level
_FC_REQUIRED_KEYS = {"type", "features"}
_GEOMETRY_REQUIRED_KEYS = {"type", "coordinates"}

# Required property keys per ML_GIS_CONTRACTS.md §2
_PROPERTIES_REQUIRED_KEYS = {
    "atm_id",
    "risk_score",
    "confidence",
    "predicted_window",
    "risk_category",
    "explanation",
}

# Required keys inside predicted_window
_WINDOW_REQUIRED_KEYS = {"start", "end"}

# Sensitive fields that MUST NOT appear in the GeoJSON properties output.
# account_id is a transaction-linked identifier; card_number/pin/cvv are never
# part of the ATM or prediction schema, but are explicitly blocked as a guard.
_SENSITIVE_FIELDS_FORBIDDEN = frozenset({"account_id", "card_number", "pin", "cvv"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_finite_float(value: Any) -> bool:
    """Return True if value can be interpreted as a finite float."""
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _check_lng_lat_bounds(lng: float, lat: float) -> Optional[str]:
    """Return an error string if [lng, lat] violates WGS84 bounds, else None."""
    if not (_LNG_MIN <= lng <= _LNG_MAX):
        return f"Longitude {lng} is out of WGS84 range [{_LNG_MIN}, {_LNG_MAX}]."
    if not (_LAT_MIN <= lat <= _LAT_MAX):
        return f"Latitude {lat} is out of WGS84 range [{_LAT_MIN}, {_LAT_MAX}]."
    return None


# ---------------------------------------------------------------------------
# Feature-level validation
# ---------------------------------------------------------------------------

def _validate_feature(feature: Any, index: int) -> List[str]:
    """Validate a single GeoJSON Feature object.

    Returns a list of error strings (empty list means the feature is valid).
    """
    errs: List[str] = []
    prefix = f"Feature[{index}]"

    if not isinstance(feature, dict):
        return [f"{prefix}: must be a dict, got {type(feature).__name__}."]

    # type field
    if feature.get("type") != "Feature":
        errs.append(f"{prefix}: 'type' must be 'Feature', got {feature.get('type')!r}.")

    # geometry
    geometry = feature.get("geometry")
    if geometry is None:
        errs.append(f"{prefix}: 'geometry' is missing.")
    elif not isinstance(geometry, dict):
        errs.append(f"{prefix}: 'geometry' must be a dict, got {type(geometry).__name__}.")
    else:
        missing_geom_keys = _GEOMETRY_REQUIRED_KEYS - geometry.keys()
        if missing_geom_keys:
            errs.append(f"{prefix}.geometry: missing required keys {sorted(missing_geom_keys)}.")
        else:
            if geometry.get("type") != "Point":
                errs.append(
                    f"{prefix}.geometry: 'type' must be 'Point', got {geometry.get('type')!r}."
                )
            coords = geometry.get("coordinates")
            if not isinstance(coords, (list, tuple)) or len(coords) < 2:
                errs.append(
                    f"{prefix}.geometry.coordinates: must be a list/tuple with at least 2 elements "
                    f"[longitude, latitude], got {coords!r}."
                )
            else:
                lng_raw, lat_raw = coords[0], coords[1]
                if not _is_finite_float(lng_raw) or not _is_finite_float(lat_raw):
                    errs.append(
                        f"{prefix}.geometry.coordinates: longitude and latitude must be finite "
                        f"numbers, got [{lng_raw!r}, {lat_raw!r}]."
                    )
                else:
                    bounds_err = _check_lng_lat_bounds(float(lng_raw), float(lat_raw))
                    if bounds_err:
                        errs.append(f"{prefix}.geometry.coordinates: {bounds_err}")

    # properties
    properties = feature.get("properties")
    if properties is None:
        errs.append(f"{prefix}: 'properties' is missing.")
    elif not isinstance(properties, dict):
        errs.append(f"{prefix}: 'properties' must be a dict, got {type(properties).__name__}.")
    else:
        missing_prop_keys = _PROPERTIES_REQUIRED_KEYS - properties.keys()
        if missing_prop_keys:
            errs.append(
                f"{prefix}.properties: missing required keys {sorted(missing_prop_keys)}."
            )

        # atm_id
        atm_id = properties.get("atm_id")
        if atm_id is not None and not isinstance(atm_id, str):
            errs.append(
                f"{prefix}.properties.atm_id: must be a string, got {type(atm_id).__name__}."
            )
        if atm_id == "":
            errs.append(f"{prefix}.properties.atm_id: must not be empty string.")

        # risk_score
        rs = properties.get("risk_score")
        if rs is not None:
            if not _is_finite_float(rs):
                errs.append(
                    f"{prefix}.properties.risk_score: must be a finite float, got {rs!r}."
                )
            else:
                rs_f = float(rs)
                if not (0.0 <= rs_f <= 1.0):
                    errs.append(
                        f"{prefix}.properties.risk_score: must be in [0.0, 1.0], got {rs_f}."
                    )

        # confidence
        conf = properties.get("confidence")
        if conf is not None:
            if not _is_finite_float(conf):
                errs.append(
                    f"{prefix}.properties.confidence: must be a finite float, got {conf!r}."
                )
            else:
                conf_f = float(conf)
                if not (0.0 <= conf_f <= 1.0):
                    errs.append(
                        f"{prefix}.properties.confidence: must be in [0.0, 1.0], got {conf_f}."
                    )

        # risk_category
        rc = properties.get("risk_category")
        if rc is not None and rc not in VALID_RISK_CATEGORIES:
            errs.append(
                f"{prefix}.properties.risk_category: must be one of "
                f"{sorted(VALID_RISK_CATEGORIES)}, got {rc!r}."
            )

        # predicted_window
        pw = properties.get("predicted_window")
        if pw is not None:
            if not isinstance(pw, dict):
                errs.append(
                    f"{prefix}.properties.predicted_window: must be a dict, "
                    f"got {type(pw).__name__}."
                )
            else:
                missing_win_keys = _WINDOW_REQUIRED_KEYS - pw.keys()
                if missing_win_keys:
                    errs.append(
                        f"{prefix}.properties.predicted_window: missing required keys "
                        f"{sorted(missing_win_keys)}."
                    )
                else:
                    for key in ("start", "end"):
                        v = pw.get(key)
                        if not isinstance(v, str):
                            errs.append(
                                f"{prefix}.properties.predicted_window.{key}: "
                                f"must be a string (ISO8601), got {type(v).__name__}."
                            )

        # explanation
        expl = properties.get("explanation")
        if expl is not None:
            if not isinstance(expl, list):
                errs.append(
                    f"{prefix}.properties.explanation: must be a list of strings, "
                    f"got {type(expl).__name__}."
                )
            else:
                for idx, item in enumerate(expl):
                    if not isinstance(item, str):
                        errs.append(
                            f"{prefix}.properties.explanation[{idx}]: must be a string, "
                            f"got {type(item).__name__}."
                        )

        # Sensitive field guard
        for sensitive_key in _SENSITIVE_FIELDS_FORBIDDEN:
            if sensitive_key in properties:
                errs.append(
                    f"{prefix}.properties: sensitive field '{sensitive_key}' must not be "
                    f"exposed in GeoJSON output."
                )

    return errs


# ---------------------------------------------------------------------------
# Public validator
# ---------------------------------------------------------------------------

def validate_predictions_geojson(geojson: Any) -> GeoJSONValidationResult:
    """Validate a GeoJSON FeatureCollection against the ML_GIS_CONTRACTS.md §2 contract.

    Checks:
      - Top-level type == "FeatureCollection" and features list is present.
      - Each Feature has type, geometry (Point with [lng, lat]), and required properties.
      - Properties contain: atm_id (str), risk_score (float [0,1]), confidence (float [0,1]),
        predicted_window ({start: ISO8601 str, end: ISO8601 str}),
        risk_category (low|medium|high), explanation (list of str).
      - Coordinates are in WGS84 bounds and use RFC 7946 [longitude, latitude] order.
      - No sensitive fields (account_id, card_number, pin, cvv) appear in properties.

    This validator is non-mutating -- it never changes the input dict.

    Args:
        geojson: The GeoJSON dict to validate (output of build_predictions_geojson()).

    Returns:
        GeoJSONValidationResult with valid=True if fully compliant, else errors listed.
    """
    errors: List[str] = []
    warnings: List[str] = []
    invalid_indices: List[int] = []

    if not isinstance(geojson, dict):
        return GeoJSONValidationResult(
            valid=False,
            errors=[f"GeoJSON root must be a dict, got {type(geojson).__name__}."],
        )

    # Top-level required keys
    missing_top = _FC_REQUIRED_KEYS - geojson.keys()
    if missing_top:
        errors.append(
            f"FeatureCollection missing required top-level keys: {sorted(missing_top)}."
        )

    # type check
    if geojson.get("type") != "FeatureCollection":
        errors.append(
            f"FeatureCollection 'type' must be 'FeatureCollection', "
            f"got {geojson.get('type')!r}."
        )

    features = geojson.get("features")
    if features is None:
        errors.append("FeatureCollection missing 'features' list.")
        return GeoJSONValidationResult(valid=False, errors=errors, warnings=warnings)

    if not isinstance(features, list):
        errors.append(
            f"FeatureCollection 'features' must be a list, got {type(features).__name__}."
        )
        return GeoJSONValidationResult(valid=False, errors=errors, warnings=warnings)

    # Validate each feature
    for i, feature in enumerate(features):
        feature_errors = _validate_feature(feature, i)
        if feature_errors:
            errors.extend(feature_errors)
            invalid_indices.append(i)

    return GeoJSONValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        feature_count=len(features),
        invalid_feature_indices=invalid_indices,
    )
