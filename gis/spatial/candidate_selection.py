"""Candidate ATM selection and proximity analysis module for CyberCast GIS layer (P3).

Implements spatial proximity analysis between a reported cybercrime location
and candidate ATM locations:
- Point-to-point crime-to-ATM physical distance calculation (Haversine, WGS84).
- Proximity-bounded candidate filtering within a caller-supplied search radius.
- Deterministic sorting by distance with secondary key tie-breaking.
- Preservation of original ATM schema fields (atm_id, location, bank, area, etc.).
- Safe handling and filtering of invalid or missing ATM coordinates.
- Cross-dataset CRS compatibility validation.

Distance values are reused by `compute_spatial_features()` (ML_GIS_CONTRACTS.md §1).
This module does not attach complete ML `spatial_features` (density is computed
separately) and does not invent risk scores or prediction probabilities.

Specified in docs/GIS_SPEC.md and docs/ML_GIS_CONTRACTS.md §1.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from gis.spatial.distance import extract_coordinates, haversine_distance
from gis.spatial.crs import (
    DEFAULT_CRS,
    validate_crs_compatibility,
    validate_wgs84_bounds,
)

logger = logging.getLogger(__name__)

# Explicit physical distance unit for all crime↔ATM proximity outputs.
DISTANCE_UNIT: str = "km"

# GIS_SPEC.md §Candidate ATM generation flow documents "e.g., 5km default search
# radius" as an example, not a ratified operational threshold. Callers (backend /
# SpatialInterface.get_candidate_atms) must pass radius_km for production use.
# This constant is the documented example default only — it is not an invented
# "nearby ATM" classification cutoff beyond that example.
DEFAULT_SEARCH_RADIUS_KM: float = 5.0


def calculate_crime_atm_distance(
    crime_location: Union[Dict[str, Any], Tuple[float, float], list],
    atm_location: Union[Dict[str, Any], Tuple[float, float], list],
) -> float:
    """Calculate the physical great-circle distance in kilometers between a crime and an ATM.

    Distance Method:
        Haversine spherical formula on WGS84 datum with Earth radius R = 6371.0088 km.

    Distance Unit:
        Kilometers (km), rounded deterministically to 4 decimal places (~0.1 meter resolution).

    Args:
        crime_location: Reported crime coordinates (dict or tuple/list).
        atm_location: Candidate ATM coordinates (dict or tuple/list).

    Returns:
        Great-circle physical distance in kilometers as float.

    Raises:
        ValueError: If either location contains invalid, out-of-bounds, or NaN coordinates.
    """
    crime_lat, crime_lng = extract_coordinates(crime_location)
    atm_lat, atm_lng = extract_coordinates(atm_location)

    validate_wgs84_bounds(crime_lat, crime_lng)
    validate_wgs84_bounds(atm_lat, atm_lng)

    return haversine_distance((crime_lat, crime_lng), (atm_lat, atm_lng))


def select_candidate_atms(
    crime_location: Dict[str, Any],
    radius_km: Optional[float] = DEFAULT_SEARCH_RADIUS_KM,
    atms: Optional[List[Dict[str, Any]]] = None,
    limit: Optional[int] = None,
    crime_crs: Optional[str] = DEFAULT_CRS,
) -> List[Dict[str, Any]]:
    """Identify and rank candidate ATMs within physical proximity of a reported cybercrime.

    Filters the full ATM dataset within radius_km, computes explicit physical distance
    in kilometers, and returns deterministic results sorted closest-first.

    Schema & Contract Conformance:
        Matches docs/GIS_SPEC.md candidate shortlist (atm_id + location) plus additive
        GIS distance fields. Does not attach ML `spatial_features` (that object also
        requires nearby_crime_density from compute_spatial_features).
        - Preserves original ATM attributes (atm_id, bank, area, historical_risk_score, ...).
        - Normalizes 'location': {'lat': float, 'lng': float}.
        - Attaches 'distance_from_crime_km' (float) and 'distance_unit' ('km').

    Args:
        crime_location: Coordinates of the reported crime (dict with 'lat'/'lng' or 'latitude'/'longitude').
        radius_km: Proximity search radius in kilometers. Defaults to the GIS_SPEC.md
                   example value (5.0 km). If None, distances are computed for all valid
                   ATMs with no cutoff. Production callers should pass this explicitly;
                   5.0 km is not a separately ratified operational threshold.
        atms: List of ATM dictionaries from database/data loader.
        limit: Optional maximum number of candidate ATMs to return.
        crime_crs: Expected CRS of crime coordinates (default: EPSG:4326).

    Returns:
        Deterministically sorted list of candidate ATM dictionaries within proximity.

    Raises:
        ValueError: If crime_location is missing/invalid, or if radius_km is <= 0.
        CRSMismatchError: If crime_location and ATM records use incompatible CRS.
    """
    if radius_km is not None and radius_km <= 0:
        raise ValueError(f"Proximity radius_km must be strictly positive (> 0). Got {radius_km}")

    if limit is not None and limit <= 0:
        raise ValueError(f"Limit must be strictly positive (> 0). Got {limit}")

    # Validate crime location coordinates (raises ValueError on null, NaN, or out-of-bounds)
    crime_lat, crime_lng = extract_coordinates(crime_location)
    validate_wgs84_bounds(crime_lat, crime_lng)
    crime_coords = (crime_lat, crime_lng)

    if not atms:
        return []

    candidates: List[Dict[str, Any]] = []

    for atm in atms:
        if not isinstance(atm, dict):
            logger.warning("Skipping non-dict ATM record: %r", atm)
            continue

        # Verify CRS compatibility if ATM record contains CRS metadata
        atm_crs = atm.get("crs", DEFAULT_CRS)
        validate_crs_compatibility(crime_crs, atm_crs, context="candidate proximity analysis")

        # Safely extract ATM coordinates
        try:
            atm_lat, atm_lng = extract_coordinates(atm)
            validate_wgs84_bounds(atm_lat, atm_lng)
        except (ValueError, TypeError) as err:
            logger.warning(
                "Skipping ATM with invalid/missing coordinates (atm_id=%s): %s",
                atm.get("atm_id"),
                err,
            )
            continue

        dist_km = calculate_crime_atm_distance(crime_coords, (atm_lat, atm_lng))

        # Apply caller-supplied proximity radius. No implicit extra cutoff is applied.
        if radius_km is not None and dist_km > radius_km:
            continue

        # Preserve original ATM fields; add normalized location + explicit-unit distance.
        # GIS_SPEC.md get_candidate_atms returns [{atm_id, location}] before the
        # backend attaches atm_historical_risk / spatial_features. Distance is
        # additive GIS output (kilometers) for ranking and for ML reuse via
        # compute_spatial_features — not a complete spatial_features object.
        candidate = dict(atm)
        candidate["location"] = {"lat": atm_lat, "lng": atm_lng}
        candidate["distance_from_crime_km"] = dist_km
        candidate["distance_unit"] = DISTANCE_UNIT

        candidates.append(candidate)

    # Deterministic sorting: primary key is distance_km, secondary key is atm_id to resolve ties
    candidates.sort(key=lambda item: (item["distance_from_crime_km"], str(item.get("atm_id", ""))))

    if limit is not None:
        candidates = candidates[:limit]

    return candidates
