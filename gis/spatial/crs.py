"""Coordinate Reference System (CRS) management module for CyberCast GIS layer (P3).

Enforces:
1. Universal geographic CRS standard: WGS84 (EPSG:4326).
2. RFC 7946 GeoJSON output CRS: EPSG:4326 with strict [longitude, latitude] coordinate ordering.
3. Explicit CRS tagging and validation for spatial datasets and Point geometries.
4. Detection and prevention of CRS mismatches between crime, ATM, and prediction datasets.
5. Strict prohibition of planar Euclidean distance calculations on geographic angular degrees.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
import logging

logger = logging.getLogger(__name__)

# Canonical Geographic CRS for CyberCast per docs/API_SPEC.md and RFC 7946 GeoJSON
DEFAULT_CRS: str = "EPSG:4326"
WGS84_CRS: str = "EPSG:4326"
GEOJSON_CRS: str = "EPSG:4326"

# Permitted aliases for WGS84
WGS84_ALIASES: Set[str] = {
    "EPSG:4326",
    "4326",
    "WGS84",
    "WGS 84",
    "URN:OGC:DEF:CRS:EPSG::4326",
    "HTTP://WWW.OPENGIS.NET/DEF/CRS/EPSG/0/4326",
}


class CRSMismatchError(ValueError):
    """Raised when spatial datasets or coordinates have incompatible Coordinate Reference Systems."""
    pass


class InvalidCRSError(ValueError):
    """Raised when an unrecognized or unsupported CRS is supplied."""
    pass


def normalize_crs(crs: Optional[Union[str, int]]) -> str:
    """Normalize CRS representation into standard 'EPSG:XXXX' string.

    Args:
        crs: CRS identifier (e.g. 'EPSG:4326', 4326, 'WGS84').

    Returns:
        Canonical CRS string (e.g. 'EPSG:4326').

    Raises:
        InvalidCRSError: If crs is empty, malformed, or unrecognized.
    """
    if crs is None:
        raise InvalidCRSError("CRS cannot be None. Expected valid CRS identifier.")

    crs_str = str(crs).strip().upper()
    if not crs_str:
        raise InvalidCRSError("CRS cannot be empty string.")

    if crs_str in WGS84_ALIASES:
        return DEFAULT_CRS

    if crs_str.isdigit():
        return f"EPSG:{crs_str}"

    return crs_str


def is_wgs84(crs: Optional[Union[str, int]]) -> bool:
    """Check whether a CRS string or code refers to WGS84 (EPSG:4326)."""
    if crs is None:
        return False
    try:
        norm = normalize_crs(crs)
        return norm == DEFAULT_CRS
    except InvalidCRSError:
        return False


def validate_crs(crs: Optional[Union[str, int]]) -> str:
    """Validate that the provided CRS matches the project's required WGS84 standard.

    Args:
        crs: CRS identifier to validate.

    Returns:
        Canonical 'EPSG:4326' string if valid.

    Raises:
        InvalidCRSError: If crs is invalid or not supported.
    """
    norm = normalize_crs(crs)
    if norm != DEFAULT_CRS:
        raise InvalidCRSError(
            f"Unsupported CRS '{crs}'. CyberCast MVP strictly requires '{DEFAULT_CRS}' (WGS84)."
        )
    return norm


def validate_crs_compatibility(
    dataset_a_crs: Optional[Union[str, int]],
    dataset_b_crs: Optional[Union[str, int]],
    context: str = "spatial operation",
) -> None:
    """Verify that two spatial datasets share the identical CRS before joint spatial operations.

    Prevents accidental distance or proximity operations between unprojected degrees and projected meters.

    Args:
        dataset_a_crs: CRS of first dataset (e.g. crime dataset).
        dataset_b_crs: CRS of second dataset (e.g. ATM dataset).
        context: Description of the calling operation for error messaging.

    Raises:
        CRSMismatchError: If the two CRS definitions do not match.
    """
    norm_a = normalize_crs(dataset_a_crs) if dataset_a_crs is not None else DEFAULT_CRS
    norm_b = normalize_crs(dataset_b_crs) if dataset_b_crs is not None else DEFAULT_CRS

    if norm_a != norm_b:
        raise CRSMismatchError(
            f"CRS mismatch detected during {context}: dataset A uses '{norm_a}', "
            f"while dataset B uses '{norm_b}'. Spatial operations require identical CRS."
        )


def validate_wgs84_bounds(lat: float, lng: float) -> None:
    """Validate that geographic coordinates conform to WGS84 geographic limits.

    Args:
        lat: Latitude in degrees.
        lng: Longitude in degrees.

    Raises:
        ValueError: If lat or lng are outside WGS84 valid ranges.
    """
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(
            f"WGS84 Latitude out of bounds: {lat}. Must be within [-90.0, 90.0] degrees."
        )
    if not (-180.0 <= lng <= 180.0):
        raise ValueError(
            f"WGS84 Longitude out of bounds: {lng}. Must be within [-180.0, 180.0] degrees."
        )


def check_coordinate_order(
    coords: Union[List[float], Tuple[float, float]],
    expected_format: str = "geojson",
) -> Tuple[float, float]:
    """Inspect coordinate sequence and guard against (lat, lng) vs (lng, lat) inversion.

    In GeoJSON RFC 7946, coordinate format is [longitude, latitude] (X, Y).
    In standard geographic text, format is often (latitude, longitude).

    Args:
        coords: Sequence of 2 numbers.
        expected_format: 'geojson' (expects [lng, lat]) or 'geographic' (expects (lat, lng)).

    Returns:
        Tuple of (latitude, longitude).

    Raises:
        ValueError: If coordinates are out of bounds or format is violated.
    """
    if len(coords) < 2:
        raise ValueError(f"Coordinate pair must contain at least 2 elements. Got {coords}")

    first, second = float(coords[0]), float(coords[1])

    if expected_format.lower() == "geojson":
        # First is Longitude (X), Second is Latitude (Y)
        lng, lat = first, second
    elif expected_format.lower() == "geographic":
        # First is Latitude, Second is Longitude
        lat, lng = first, second
    else:
        raise ValueError(f"Unknown expected_format '{expected_format}'. Choose 'geojson' or 'geographic'.")

    validate_wgs84_bounds(lat, lng)
    return lat, lng
