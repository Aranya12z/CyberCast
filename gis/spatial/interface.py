"""Spatial interface abstract base class for CyberCast GIS layer.

Defines the contract between the backend application layer and the spatial analytics module.
Specified in docs/GIS_SPEC.md and docs/ML_GIS_CONTRACTS.md §2.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SpatialInterface(ABC):
    """Stateless spatial interface consumed by the backend domain orchestration layer.

    Per docs/GIS_SPEC.md, this module is stateless and does not query the database directly;
    the backend fetches ATMs and recent crimes and supplies them as arguments.
    """

    @abstractmethod
    def get_candidate_atms(
        self, crime_location: Dict[str, Any], radius_km: float, atms: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter candidate ATMs within radius_km of the crime location.

        Args:
            crime_location: Dict with coordinates (e.g. {'lat': float, 'lng': float}).
            radius_km: Search radius in kilometers (e.g. 5.0).
            atms: Full list of ATMs fetched by the backend from the `atms` table.

        Returns:
            Subset of ATMs within radius_km as a list of dicts. Feeds ML's candidate_atms input.
        """
        pass

    @abstractmethod
    def compute_spatial_features(
        self,
        crime_location: Dict[str, Any],
        atm_location: Dict[str, Any],
        historical_crimes: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Compute spatial features for one ATM relative to the crime and historical crimes.

        Args:
            crime_location: Reported crime coordinates.
            atm_location: Candidate ATM coordinates.
            historical_crimes: Recent crime events fetched by the backend from the `crimes` table.

        Returns:
            Dict matching ML_GIS_CONTRACTS.md §1:
            {
                "distance_from_crime": float,
                "nearby_crime_density": float
            }
        """
        pass

    @abstractmethod
    def to_geojson(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert backend-merged prediction results into a standard GeoJSON FeatureCollection.

        Args:
            predictions: List of prediction result dicts containing at minimum:
                - atm_id: str
                - location: {'lat': float, 'lng': float} (or direct lat/lng)
                - risk_score: float [0, 1]
                - confidence: float [0, 1]
                - predicted_window: {'start': str, 'end': str}
                - explanation: list of strings or list of feature contribution dicts

        Returns:
            RFC 7946 compliant GeoJSON FeatureCollection matching ML_GIS_CONTRACTS.md §2.
        """
        pass
