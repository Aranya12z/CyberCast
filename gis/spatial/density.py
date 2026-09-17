"""Spatial feature computation and crime density module for CyberCast GIS layer.

Computes spatial features consumed by the ML prediction engine:
- distance_from_crime (km): Great-circle distance from crime location to candidate ATM.
- nearby_crime_density: Number of historical crime incidents within a neighborhood radius.
Specified in docs/GIS_SPEC.md and docs/ML_GIS_CONTRACTS.md §1.
"""

from typing import Any, Dict, List
import logging

from gis.spatial.distance import extract_coordinates, haversine_distance

logger = logging.getLogger(__name__)

# Default neighborhood radius for crime density calculation (in kilometers)
DEFAULT_DENSITY_RADIUS_KM: float = 2.0


def compute_nearby_crime_density(
    atm_location: Dict[str, Any],
    historical_crimes: List[Dict[str, Any]] = None,
    density_radius_km: float = DEFAULT_DENSITY_RADIUS_KM,
) -> float:
    """Calculate the crime density around an ATM location.

    Counts historical crime incidents occurring within density_radius_km of the ATM.

    Args:
        atm_location: Coordinates of the ATM.
        historical_crimes: List of historical crime records from the `crimes` table.
        density_radius_km: Radius in kilometers defining the local neighborhood. Default is 2.0 km.

    Returns:
        Float count of historical crimes within the neighborhood radius.
    """
    if not historical_crimes:
        return 0.0

    atm_lat, atm_lng = extract_coordinates(atm_location)
    atm_coords = (atm_lat, atm_lng)

    count = 0
    for crime in historical_crimes:
        if not isinstance(crime, dict):
            continue

        try:
            crime_coords = extract_coordinates(crime)
        except (ValueError, TypeError):
            # Skip invalid crime locations gracefully
            continue

        dist_km = haversine_distance(atm_coords, crime_coords)
        if dist_km <= density_radius_km:
            count += 1

    return float(count)


def compute_spatial_features(
    crime_location: Dict[str, Any],
    atm_location: Dict[str, Any],
    historical_crimes: List[Dict[str, Any]] = None,
    density_radius_km: float = DEFAULT_DENSITY_RADIUS_KM,
) -> Dict[str, float]:
    """Compute spatial features for one candidate ATM relative to reported crime and history.

    Args:
        crime_location: Location of the reported cybercrime.
        atm_location: Location of the candidate ATM.
        historical_crimes: List of historical crime incidents.
        density_radius_km: Neighborhood radius in km for density calculation. Default is 2.0 km.

    Returns:
        Dict strictly matching ML_GIS_CONTRACTS.md §1:
        {
            "distance_from_crime": float,
            "nearby_crime_density": float
        }
    """
    # Validate coordinates
    crime_coords = extract_coordinates(crime_location)
    atm_coords = extract_coordinates(atm_location)

    distance_from_crime = haversine_distance(crime_coords, atm_coords)
    nearby_crime_density = compute_nearby_crime_density(
        atm_location=atm_coords,
        historical_crimes=historical_crimes or [],
        density_radius_km=density_radius_km,
    )

    return {
        "distance_from_crime": distance_from_crime,
        "nearby_crime_density": nearby_crime_density,
    }
