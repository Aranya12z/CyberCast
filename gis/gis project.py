"""CyberCast GIS / Spatial Analytics Layer (P3).

Implements spatial candidate selection, Haversine distance, crime density computation,
hotspot clustering, and GeoJSON generation for the CyberCast system.
"""

from gis.spatial.service import SpatialService
from gis.spatial.interface import SpatialInterface
from gis.spatial.distance import haversine_distance, extract_coordinates
from gis.spatial.candidate_selection import (
    select_candidate_atms,
    calculate_crime_atm_distance,
    DEFAULT_SEARCH_RADIUS_KM,
    DISTANCE_UNIT,
)
from gis.spatial.geojson_builder import build_predictions_geojson, categorize_risk
from gis.spatial.data_loader import SpatialPoint, load_crimes, load_atms
from gis.spatial.crs import (
    DEFAULT_CRS,
    WGS84_CRS,
    GEOJSON_CRS,
    validate_crs,
    validate_crs_compatibility,
    CRSMismatchError,
    InvalidCRSError,
)

__all__ = [
    "SpatialService",
    "SpatialInterface",
    "haversine_distance",
    "extract_coordinates",
    "select_candidate_atms",
    "calculate_crime_atm_distance",
    "DEFAULT_SEARCH_RADIUS_KM",
    "DISTANCE_UNIT",
    "build_predictions_geojson",
    "categorize_risk",
    "SpatialPoint",
    "load_crimes",
    "load_atms",
    "DEFAULT_CRS",
    "WGS84_CRS",
    "GEOJSON_CRS",
    "validate_crs",
    "validate_crs_compatibility",
    "CRSMismatchError",
    "InvalidCRSError",
]
