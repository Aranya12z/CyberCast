"""Geospatial distance and coordinate validation module for CyberCast GIS layer.

All spatial coordinates use the WGS84 geographic coordinate reference system (EPSG:4326).
Physical distances on the Earth's surface are calculated using the Haversine great-circle
formula with a mean Earth radius of 6,371.0088 kilometers.
"""

import math
from typing import Any, Dict, Tuple, Union

# WGS84 mean earth radius in kilometers
EARTH_RADIUS_KM: float = 6371.0088


def extract_coordinates(location: Union[Dict[str, Any], Tuple[float, float], list]) -> Tuple[float, float]:
    """Extract and validate (latitude, longitude) from various input formats.

    Supported formats:
        - dict with keys 'lat' and 'lng'
        - dict with keys 'latitude' and 'longitude'
        - dict with key 'location' containing one of the above
        - tuple or list of (latitude, longitude)

    Args:
        location: The location representation.

    Returns:
        Tuple of (latitude, longitude) as floats.

    Raises:
        ValueError: If coordinates are missing, non-numeric, or outside valid WGS84 ranges.
    """
    if location is None:
        raise ValueError("Location cannot be None.")

    # Handle nested location dict: {"location": {"lat": ..., "lng": ...}}
    if isinstance(location, dict) and "location" in location and isinstance(location["location"], (dict, tuple, list)):
        location = location["location"]

    lat: float
    lng: float

    if isinstance(location, dict):
        if "lat" in location and "lng" in location:
            raw_lat = location["lat"]
            raw_lng = location["lng"]
        elif "latitude" in location and "longitude" in location:
            raw_lat = location["latitude"]
            raw_lng = location["longitude"]
        elif "lat" in location and "lon" in location:
            raw_lat = location["lat"]
            raw_lng = location["lon"]
        else:
            raise ValueError(
                f"Location dict must contain ('lat', 'lng') or ('latitude', 'longitude'). Got keys: {list(location.keys())}"
            )
    elif isinstance(location, (tuple, list)):
        if len(location) < 2:
            raise ValueError(f"Coordinate sequence must contain at least 2 elements (lat, lng). Got {len(location)} elements.")
        raw_lat = location[0]
        raw_lng = location[1]
    else:
        raise ValueError(f"Unsupported location format: {type(location)}. Expected dict, tuple, or list.")

    try:
        lat = float(raw_lat)
        lng = float(raw_lng)
    except (TypeError, ValueError) as err:
        raise ValueError(f"Coordinates must be numeric. Got lat={raw_lat!r}, lng={raw_lng!r}") from err

    if math.isnan(lat) or math.isnan(lng) or math.isinf(lat) or math.isinf(lng):
        raise ValueError(f"Coordinates cannot be NaN or Infinite. Got lat={lat}, lng={lng}")

    # Validate WGS84 geographic boundaries
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude must be between -90.0 and 90.0 degrees. Got {lat}")
    if not (-180.0 <= lng <= 180.0):
        raise ValueError(f"Longitude must be between -180.0 and 180.0 degrees. Got {lng}")

    return lat, lng


def haversine_distance(
    loc1: Union[Dict[str, Any], Tuple[float, float], list],
    loc2: Union[Dict[str, Any], Tuple[float, float], list],
    radius_km: float = EARTH_RADIUS_KM,
) -> float:
    """Calculate the great-circle distance between two geographic points using Haversine formula.

    Formula:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlng/2)
        c = 2 * atan2(√a, √(1-a))
        d = R * c

    Args:
        loc1: Starting location (dict with lat/lng, or (lat, lng)).
        loc2: Ending location (dict with lat/lng, or (lat, lng)).
        radius_km: Earth radius in kilometers (default: 6371.0088 km).

    Returns:
        Great-circle distance in kilometers (rounded to 4 decimal places).
    """
    lat1, lng1 = extract_coordinates(loc1)
    lat2, lng2 = extract_coordinates(loc2)

    # Identical points check for exact 0.0
    if lat1 == lat2 and lng1 == lng2:
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (math.sin(delta_phi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)

    # Clip 'a' to [0.0, 1.0] to guard against floating-point inaccuracy at antipodes
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = radius_km * c
    return round(distance, 4)
