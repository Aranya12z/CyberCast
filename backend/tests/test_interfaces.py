"""
backend/tests/test_interfaces.py — Tests for ModelInterface, MockModelInterface,
and SpatialInterface / SpatialService integration.
"""
from datetime import datetime, timezone
import pytest

from app.interfaces.model_interface import MockModelInterface, ModelInterface
from app.interfaces.spatial_interface import SpatialService, get_spatial_service
from app.schemas.prediction import PredictionResponse


def test_mock_model_interface_deterministic_prediction():
    """Verify MockModelInterface scores candidates over the 9 contract features."""
    mock_model = MockModelInterface(top_k=3, confidence_threshold=0.35)

    payload = {
        "crime": {
            "crime_id": "c1111111-1111-1111-1111-111111111111",
            "crime_type": "atm_fraud",
            "timestamp": "2026-09-18T10:00:00Z",
            "location": {"lat": 12.9716, "lng": 77.5946},
            "amount": 75000.0,
        },
        "candidate_atms": [
            {
                "atm_id": "a1111111-1111-1111-1111-111111111111",
                "location": {"lat": 12.9720, "lng": 77.5950},
                "atm_historical_risk": 0.65,
                "spatial_features": {
                    "distance_from_crime": 0.5,
                    "nearby_crime_density": 3.2,
                },
            },
            {
                "atm_id": "a2222222-2222-2222-2222-222222222222",
                "location": {"lat": 12.9800, "lng": 77.6000},
                "atm_historical_risk": 0.20,
                "spatial_features": {
                    "distance_from_crime": 2.5,
                    "nearby_crime_density": 1.0,
                },
            },
            {
                "atm_id": "a3333333-3333-3333-3333-333333333333",
                "location": {"lat": 13.0000, "lng": 77.6200},
                "atm_historical_risk": 0.10,
                "spatial_features": {
                    "distance_from_crime": 8.0,
                    "nearby_crime_density": 0.2,
                },
            },
        ],
        "recent_transactions": [
            {
                "atm_id": "a1111111-1111-1111-1111-111111111111",
                "timestamp": "2026-09-18T09:30:00Z",
                "amount": 10000.0,
            },
            {
                "atm_id": "a1111111-1111-1111-1111-111111111111",
                "timestamp": "2026-09-18T08:00:00Z",
                "amount": 5000.0,
            },
        ],
    }

    result = mock_model.predict(payload)

    assert result["status"] == "ok"
    assert result["model_version"] == "mock_rf_v1.0.0"
    assert len(result["predictions"]) == 3

    # Ranking: ATM 1 (closest, high historical risk, recent txns) must rank first
    first = result["predictions"][0]
    second = result["predictions"][1]
    assert first["atm_id"] == "a1111111-1111-1111-1111-111111111111"
    assert first["risk_score"] > second["risk_score"]
    assert first["confidence"] >= 0.35

    # Predicted window: 6-hour window per ADR-005
    assert "start" in first["predicted_window"]
    assert "end" in first["predicted_window"]

    # Explanations: high/medium/low labels
    assert len(first["explanation"]) > 0
    for exp in first["explanation"]:
        assert exp["contribution"] in ["high", "medium", "low"]
        assert "feature" in exp
        assert "value" in exp

    # Validate output schema against Pydantic model
    validated = PredictionResponse(
        crime_id=payload["crime"]["crime_id"],
        generated_at=datetime.now(timezone.utc),
        model_version=result["model_version"],
        predictions=result["predictions"],
        status=result["status"],
    )
    assert validated.status == "ok"


def test_mock_model_interface_low_confidence_threshold():
    """Verify confidence < 0.35 triggers insufficient_confidence and empty predictions."""
    mock_model = MockModelInterface(confidence_threshold=0.35)

    # Candidate with distant location and zero activity (low confidence)
    payload = {
        "crime": {
            "crime_id": "c1111111-1111-1111-1111-111111111111",
            "crime_type": "atm_fraud",
            "timestamp": "2026-09-18T10:00:00Z",
            "location": {"lat": 12.9716, "lng": 77.5946},
            "amount": 1000.0,
        },
        "candidate_atms": [
            {
                "atm_id": "a_far",
                "location": {"lat": 13.5000, "lng": 78.5000},
                "atm_historical_risk": 0.0,
                "spatial_features": {
                    "distance_from_crime": 25.0,  # very far -> low confidence
                    "nearby_crime_density": 0.0,
                },
            }
        ],
        "recent_transactions": [],
    }

    result = mock_model.predict(payload)
    assert result["status"] == "insufficient_confidence"
    assert result["predictions"] == []


def test_mock_model_interface_empty_candidates():
    """Verify empty candidates returns insufficient_evidence."""
    mock_model = MockModelInterface()
    result = mock_model.predict({"crime": {"crime_id": "c1"}, "candidate_atms": []})
    assert result["status"] == "insufficient_evidence"
    assert result["predictions"] == []


def test_spatial_service_integration():
    """Verify that gis.spatial.service.SpatialService is wired into the backend by import."""
    spatial_svc = get_spatial_service(default_search_radius_km=5.0)
    assert isinstance(spatial_svc, SpatialService)

    # Test candidate selection
    crime_loc = {"lat": 12.9716, "lng": 77.5946}
    atms = [
        {"atm_id": "atm-near", "latitude": 12.9720, "longitude": 77.5950, "bank": "SBI", "area": "MG Rd"},
        {"atm_id": "atm-far", "latitude": 13.5000, "longitude": 78.5000, "bank": "HDFC", "area": "Outskirts"},
    ]
    candidates = spatial_svc.get_candidate_atms(crime_location=crime_loc, radius_km=5.0, atms=atms)
    assert len(candidates) == 1
    assert candidates[0]["atm_id"] == "atm-near"

    # Test spatial features computation
    features = spatial_svc.compute_spatial_features(
        crime_location=crime_loc,
        atm_location={"lat": 12.9720, "lng": 77.5950},
        historical_crimes=[{"latitude": 12.9725, "longitude": 77.5955}],
    )
    assert "distance_from_crime" in features
    assert "nearby_crime_density" in features
    assert features["distance_from_crime"] > 0.0

    # Test GeoJSON export
    predictions = [
        {
            "atm_id": "atm-near",
            "location": {"lat": 12.9720, "lng": 77.5950},
            "risk_score": 0.85,
            "confidence": 0.75,
            "predicted_window": {"start": "2026-09-18T10:00:00Z", "end": "2026-09-18T16:00:00Z"},
            "explanation": [{"feature": "distance_from_crime", "value": 0.5, "contribution": "high"}],
        }
    ]
    geojson = spatial_svc.to_geojson(predictions)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1
    props = geojson["features"][0]["properties"]
    assert props["atm_id"] == "atm-near"
    assert props["risk_score"] == 0.85
    assert props["confidence"] == 0.75
    assert props["risk_category"] == "high"
