"""Concrete SpatialService implementation for CyberCast GIS layer.

Implements SpatialInterface as defined in docs/GIS_SPEC.md and docs/ML_GIS_CONTRACTS.md §2.
Stateless service consumed by the backend orchestration layer.
"""

from typing import Any, Dict, List, Optional

from gis.spatial.interface import SpatialInterface
from gis.spatial.distance import haversine_distance, extract_coordinates
from gis.spatial.candidate_selection import select_candidate_atms, DEFAULT_SEARCH_RADIUS_KM
from gis.spatial.density import compute_spatial_features, compute_nearby_crime_density, DEFAULT_DENSITY_RADIUS_KM
from gis.spatial.hotspots import detect_spatial_hotspots
from gis.spatial.geojson_builder import build_predictions_geojson, categorize_risk


class SpatialService(SpatialInterface):
    """Stateless concrete implementation of the GIS SpatialInterface."""

    def __init__(
        self,
        default_search_radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
        default_density_radius_km: float = DEFAULT_DENSITY_RADIUS_KM,
    ) -> None:
        """Initialize SpatialService with configurable default search parameters.

        Args:
            default_search_radius_km: Default radius for candidate ATM proximity search.
            default_density_radius_km: Default radius for nearby crime density computation.
        """
        self.default_search_radius_km = default_search_radius_km
        self.default_density_radius_km = default_density_radius_km

    def get_candidate_atms(
        self,
        crime_location: Dict[str, Any],
        radius_km: Optional[float] = None,
        atms: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Filter ATMs located within radius_km of the crime location.

        Args:
            crime_location: Crime coordinates dict (e.g. {'lat': 28.6139, 'lng': 77.2090}).
            radius_km: Search radius in kilometers. Required by GIS_SPEC.md SpatialInterface.
                If omitted, uses the GIS_SPEC example default (5.0 km) — not a separately
                ratified operational cutoff. Pass this explicitly in production.
            atms: Full list of ATMs fetched from the database by the backend.

        Returns:
            List of candidate ATM dicts within radius_km, sorted by proximity to crime.
        """
        effective_radius = radius_km if radius_km is not None else self.default_search_radius_km
        return select_candidate_atms(
            crime_location=crime_location,
            radius_km=effective_radius,
            atms=atms or [],
        )

    def compute_spatial_features(
        self,
        crime_location: Dict[str, Any],
        atm_location: Dict[str, Any],
        historical_crimes: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, float]:
        """Compute spatial features for one ATM relative to the crime and historical crimes.

        Args:
            crime_location: Reported crime coordinates.
            atm_location: Candidate ATM coordinates.
            historical_crimes: Recent crimes from database for density calculation.

        Returns:
            Dict matching ML_GIS_CONTRACTS.md §1:
            {
                "distance_from_crime": float,
                "nearby_crime_density": float
            }
        """
        return compute_spatial_features(
            crime_location=crime_location,
            atm_location=atm_location,
            historical_crimes=historical_crimes or [],
            density_radius_km=self.default_density_radius_km,
        )

    def to_geojson(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert prediction results into RFC 7946 GeoJSON FeatureCollection.

        Args:
            predictions: List of prediction result dicts.

        Returns:
            GeoJSON FeatureCollection dict strictly matching ML_GIS_CONTRACTS.md §2.
        """
        return build_predictions_geojson(predictions or [])

    def calculate_distance(
        self,
        loc1: Any,
        loc2: Any,
    ) -> float:
        """Calculate great-circle Haversine distance between two points in kilometers."""
        return haversine_distance(loc1, loc2)

    def detect_hotspots(
        self,
        incidents: List[Dict[str, Any]],
        eps_km: float = 1.5,
        min_samples: int = 3,
    ) -> List[Dict[str, Any]]:
        """Detect crime or cash-out hotspots using spatial density clustering."""
        return detect_spatial_hotspots(
            incidents=incidents or [],
            eps_km=eps_km,
            min_samples=min_samples,
        )

    def get_risk_category(self, risk_score: float) -> str:
        """Map risk score to categorical level ('low', 'medium', 'high')."""
        return categorize_risk(risk_score)
