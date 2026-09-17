"""CyberCast GIS Spatial module."""

from gis.spatial.interface import SpatialInterface
from gis.spatial.service import SpatialService
from gis.spatial.distance import haversine_distance, extract_coordinates, EARTH_RADIUS_KM
from gis.spatial.candidate_selection import (
    select_candidate_atms,
    calculate_crime_atm_distance,
    DEFAULT_SEARCH_RADIUS_KM,
    DISTANCE_UNIT,
)
from gis.spatial.density import compute_spatial_features, compute_nearby_crime_density
from gis.spatial.hotspots import detect_spatial_hotspots
from gis.spatial.geojson_builder import build_predictions_geojson, categorize_risk
from gis.spatial.data_loader import (
    SpatialPoint,
    load_crimes,
    load_atms,
    prepare_spatial_record,
)
from gis.spatial.crs import (
    DEFAULT_CRS,
    WGS84_CRS,
    GEOJSON_CRS,
    validate_crs,
    validate_crs_compatibility,
    is_wgs84,
    check_coordinate_order,
    CRSMismatchError,
    InvalidCRSError,
)

__all__ = [
    "SpatialInterface",
    "SpatialService",
    "haversine_distance",
    "extract_coordinates",
    "EARTH_RADIUS_KM",
    "select_candidate_atms",
    "calculate_crime_atm_distance",
    "DEFAULT_SEARCH_RADIUS_KM",
    "DISTANCE_UNIT",
    "compute_spatial_features",
    "compute_nearby_crime_density",
    "detect_spatial_hotspots",
    "build_predictions_geojson",
    "categorize_risk",
    "SpatialPoint",
    "load_crimes",
    "load_atms",
    "prepare_spatial_record",
    "DEFAULT_CRS",
    "WGS84_CRS",
    "GEOJSON_CRS",
    "validate_crs",
    "validate_crs_compatibility",
    "is_wgs84",
    "check_coordinate_order",
    "CRSMismatchError",
    "InvalidCRSError",
]
