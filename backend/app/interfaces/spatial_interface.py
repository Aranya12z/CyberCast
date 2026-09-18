"""
app/interfaces/spatial_interface.py — Geospatial interface & concrete SpatialService import.

Reference: GIS_SPEC.md §Interface and ML_GIS_CONTRACTS.md §2 (GIS ↔ Backend Contract)
Owner: P3 (GIS side). P5 (Backend) consumes P3's SpatialService by import.
"""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repository root is in sys.path so 'gis' package is importable
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from gis.spatial.interface import SpatialInterface as GisSpatialInterface
from gis.spatial.service import SpatialService


class SpatialInterface(ABC):
    """
    Abstract interface for spatial calculations.
    Stateless function library — does not directly query the database.
    Backend fetches data and supplies it as arguments.
    """

    @abstractmethod
    def get_candidate_atms(
        self,
        crime_location: Dict[str, float],
        radius_km: Optional[float] = None,
        atms: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter full ATM list to those within radius_km of crime_location.
        Returns subset as [{"atm_id": str, "location": {"lat": float, "lng": float}}].
        """
        pass

    @abstractmethod
    def compute_spatial_features(
        self,
        crime_location: Dict[str, float],
        atm_location: Dict[str, float],
        historical_crimes: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, float]:
        """
        Compute spatial features for one candidate ATM relative to a crime and historical crimes.
        Returns {"distance_from_crime": float, "nearby_crime_density": float}.
        """
        pass

    @abstractmethod
    def to_geojson(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Converts prediction result dicts into GeoJSON FeatureCollection format
        per ML_GIS_CONTRACTS.md §2.
        """
        pass


def get_spatial_service(
    default_search_radius_km: float = 5.0,
    default_density_radius_km: float = 3.0,
) -> SpatialService:
    """
    Factory function returning the concrete GIS SpatialService instance.
    Wired directly from gis/spatial/service.py by import.
    """
    return SpatialService(
        default_search_radius_km=default_search_radius_km,
        default_density_radius_km=default_density_radius_km,
    )
