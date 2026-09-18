"""GeoJSON FeatureCollection builder module for CyberCast GIS layer.

Converts prediction results into RFC 7946 compliant GeoJSON FeatureCollection
consumed by the frontend React-Leaflet map UI.
Strictly adheres to docs/ML_GIS_CONTRACTS.md §2 and docs/ADRS.md ADR-006.
"""

from typing import Any, Dict, List, Union
import logging

from gis.spatial.distance import extract_coordinates

logger = logging.getLogger(__name__)


def categorize_risk(risk_score: float) -> str:
    """Bucket risk score into categorical level per docs/GIS_SPEC.md and docs/ADRS.md ADR-006.

    Thresholds:
        risk_score >= 0.7        -> "high"
        0.4 <= risk_score < 0.7  -> "medium"
        risk_score < 0.4         -> "low"

    Args:
        risk_score: Float in range [0.0, 1.0].

    Returns:
        Risk category string: 'low', 'medium', or 'high'.
    """
    if risk_score >= 0.7:
        return "high"
    elif risk_score >= 0.4:
        return "medium"
    else:
        return "low"


def format_explanation(explanation_raw: Any) -> List[str]:
    """Format explanation entries into a list of human-readable strings.

    Handles:
        - List of strings: preserved as-is.
        - List of dicts (e.g. from ML inference: [{'feature': ..., 'value': ..., 'contribution': ...}]).
        - None or empty: returns [].

    Args:
        explanation_raw: The explanation attribute from prediction output.

    Returns:
        List of human-readable explanation strings.
    """
    if not explanation_raw:
        return []

    if isinstance(explanation_raw, str):
        return [explanation_raw]

    formatted: List[str] = []
    for item in explanation_raw:
        if isinstance(item, str):
            formatted.append(item)
        elif isinstance(item, dict):
            feature = item.get("feature", "feature")
            val = item.get("value", "")
            contrib = item.get("contribution", "")

            # Format feature names nicely
            feature_display = feature.replace("_", " ").title()

            if feature == "distance_from_crime":
                msg = f"Distance from crime: {val} km ({contrib} contribution)"
            elif feature == "nearby_crime_density":
                msg = f"Nearby crime density: {val} incidents ({contrib} contribution)"
            elif contrib:
                msg = f"{feature_display}: {val} ({contrib} contribution)"
            else:
                msg = f"{feature_display}: {val}"
            formatted.append(msg)
        else:
            formatted.append(str(item))

    return formatted


def build_predictions_geojson(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert backend-merged prediction records into RFC 7946 GeoJSON FeatureCollection.

    Contract: docs/ML_GIS_CONTRACTS.md §2:
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": { "type": "Point", "coordinates": [longitude, latitude] },
          "properties": {
            "atm_id": "string",
            "risk_score": 0.0,
            "confidence": 0.0,
            "predicted_window": { "start": "ISO8601", "end": "ISO8601" },
            "risk_category": "low|medium|high",
            "explanation": ["string"]
          }
        }
      ]
    }

    Args:
        predictions: List of prediction result records with coordinates.

    Returns:
        Contract-compliant GeoJSON FeatureCollection dictionary.
    """
    features: List[Dict[str, Any]] = []

    if not predictions:
        return {
            "type": "FeatureCollection",
            "features": [],
        }

    for pred in predictions:
        if not isinstance(pred, dict):
            continue

        try:
            lat, lng = extract_coordinates(pred)
        except (ValueError, TypeError) as err:
            logger.warning("Skipping prediction record with invalid coordinates (atm_id=%s): %s", pred.get("atm_id"), err)
            continue

        risk_score = float(pred.get("risk_score", 0.0))
        confidence = float(pred.get("confidence", 0.0))
        risk_category = pred.get("risk_category") or categorize_risk(risk_score)
        explanation = format_explanation(pred.get("explanation"))

        predicted_window = pred.get("predicted_window")
        if not isinstance(predicted_window, dict):
            predicted_window = {"start": "", "end": ""}

        feature_properties = {
            "atm_id": str(pred.get("atm_id", "")),
            "risk_score": round(risk_score, 4),
            "confidence": round(confidence, 4),
            "predicted_window": {
                "start": str(predicted_window.get("start", "")),
                "end": str(predicted_window.get("end", "")),
            },
            "risk_category": risk_category,
            "explanation": explanation,
        }

        # Optionally preserve metadata fields if present (bank, area) without breaking contract
        if "bank" in pred and pred["bank"] is not None:
            feature_properties["bank"] = str(pred["bank"])
        if "area" in pred and pred["area"] is not None:
            feature_properties["area"] = str(pred["area"])

        feature = {
            "type": "Feature",
            # RFC 7946 GeoJSON requires [longitude, latitude]
            "geometry": {
                "type": "Point",
                "coordinates": [lng, lat],
            },
            "properties": feature_properties,
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }
