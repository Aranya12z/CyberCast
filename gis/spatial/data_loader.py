"""Geospatial data loading and preparation module for CyberCast GIS layer (P3).

Handles:
- Ingestion of crime and ATM data from CSV files, JSON files, or in-memory record sequences.
- Conversion of (latitude, longitude) into standardized WGS84 SpatialPoint geometries.
- Robust validation and filtering of missing, null, or out-of-bounds coordinates.
- Full preservation of existing contract field names per docs/DATA_SCHEMA.md.
"""

import csv
import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from gis.spatial.distance import extract_coordinates
from gis.spatial.crs import DEFAULT_CRS, validate_crs, validate_crs_compatibility, InvalidCRSError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpatialPoint:
    """Immutable spatial Point geometry representation in WGS84 (EPSG:4326).

    In accordance with OGC standards and RFC 7946 GeoJSON:
    - x corresponds to Longitude (easting)
    - y corresponds to Latitude (northing)
    - Coordinates sequence is [x, y] -> [longitude, latitude]
    - Coordinate Reference System is explicit (default: EPSG:4326)
    """

    x: float  # Longitude in degrees [-180.0, 180.0]
    y: float  # Latitude in degrees [-90.0, 90.0]
    crs: str = DEFAULT_CRS  # Explicit CRS identifier

    def __post_init__(self) -> None:
        """Validate WGS84 coordinate bounds and CRS upon creation."""
        validate_crs(self.crs)
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise TypeError(f"Coordinates must be numeric. Got x={self.x!r}, y={self.y!r}")
        if math.isnan(self.x) or math.isnan(self.y) or math.isinf(self.x) or math.isinf(self.y):
            raise ValueError(f"Coordinates cannot be NaN or Infinite. Got x={self.x}, y={self.y}")
        if not (-180.0 <= self.x <= 180.0):
            raise ValueError(f"Longitude (x) must be between -180.0 and 180.0 degrees. Got {self.x}")
        if not (-90.0 <= self.y <= 90.0):
            raise ValueError(f"Latitude (y) must be between -90.0 and 90.0 degrees. Got {self.y}")

    @property
    def lng(self) -> float:
        """Longitude in degrees."""
        return self.x

    @property
    def lat(self) -> float:
        """Latitude in degrees."""
        return self.y

    @property
    def coordinates(self) -> List[float]:
        """RFC 7946 GeoJSON coordinate pair: [longitude, latitude]."""
        return [self.x, self.y]

    def to_dict(self) -> Dict[str, float]:
        """Convert to standard API location dictionary format."""
        return {"lat": self.y, "lng": self.x}

    def to_geojson_geometry(self) -> Dict[str, Any]:
        """Convert to GeoJSON Point geometry dictionary."""
        return {
            "type": "Point",
            "coordinates": [self.x, self.y],
        }

    def to_shapely(self) -> Any:
        """Convert to Shapely Point geometry if shapely is installed."""
        try:
            from shapely.geometry import Point
            return Point(self.x, self.y)
        except ImportError:
            raise ImportError("Shapely is not installed in the current environment.")


def prepare_spatial_record(
    record: Dict[str, Any],
    lat_field: Optional[str] = None,
    lng_field: Optional[str] = None,
    strict: bool = False,
    crs: Optional[Union[str, int]] = DEFAULT_CRS,
) -> Optional[Dict[str, Any]]:
    """Convert raw entity record to a prepared spatial record with SpatialPoint geometry.

    Preserves all original fields and adds:
    - 'geometry': SpatialPoint(x=lng, y=lat, crs=crs)
    - 'location': {'lat': lat, 'lng': lng} (standardized format)
    - 'crs': 'EPSG:4326' (explicit CRS metadata)

    Args:
        record: Raw data dict.
        lat_field: Explicit field name for latitude if custom.
        lng_field: Explicit field name for longitude if custom.
        strict: If True, raises ValueError on invalid coordinates or CRS. If False, returns None.
        crs: Coordinate Reference System identifier (default: EPSG:4326).

    Returns:
        Prepared record dict, or None if coordinates are missing/invalid and strict=False.
    """
    if not isinstance(record, dict):
        if strict:
            raise TypeError(f"Record must be a dict, got {type(record)}")
        return None

    try:
        validated_crs = validate_crs(crs if crs is not None else DEFAULT_CRS)
    except (InvalidCRSError, ValueError) as err:
        if strict:
            raise InvalidCRSError(f"Invalid CRS for spatial record: {err}") from err
        logger.warning("Skipping record with invalid CRS: %s", err)
        return None

    # Handle explicit custom fields
    if lat_field and lng_field:
        if lat_field not in record or lng_field not in record:
            if strict:
                raise ValueError(f"Record missing specified fields '{lat_field}' or '{lng_field}'")
            return None
        raw_lat = record[lat_field]
        raw_lng = record[lng_field]
        location_source = {"lat": raw_lat, "lng": raw_lng}
    else:
        location_source = record

    try:
        lat, lng = extract_coordinates(location_source)
        point = SpatialPoint(x=lng, y=lat, crs=validated_crs)
    except (ValueError, TypeError) as err:
        if strict:
            raise ValueError(f"Invalid coordinates in record: {err}") from err
        logger.warning("Skipping record with invalid coordinates: %s", err)
        return None

    # Copy record to avoid mutating caller's dict
    prepared = dict(record)
    prepared["geometry"] = point
    prepared["location"] = point.to_dict()
    # Retain explicit latitude and longitude fields matching DATA_SCHEMA.md
    prepared["latitude"] = lat
    prepared["longitude"] = lng
    prepared["crs"] = validated_crs

    return prepared


def _load_raw_data(source: Union[str, Path, List[Dict[str, Any]], Iterable[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Load raw records from CSV path, JSON path, or in-memory record list."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Source file does not exist: {path}")

        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "crimes" in data:
                    return data["crimes"]
                elif isinstance(data, dict) and "atms" in data:
                    return data["atms"]
                elif isinstance(data, dict) and "features" in data:
                    # GeoJSON format
                    records = []
                    for feat in data["features"]:
                        props = feat.get("properties", {})
                        geom = feat.get("geometry", {})
                        if geom.get("type") == "Point" and "coordinates" in geom:
                            props["longitude"] = geom["coordinates"][0]
                            props["latitude"] = geom["coordinates"][1]
                        records.append(props)
                    return records
                else:
                    raise ValueError(f"Unexpected JSON structure in {path}")
        elif path.suffix.lower() == ".csv":
            records = []
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            return records
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}. Expected .csv or .json")
    elif isinstance(source, list):
        return list(source)
    elif hasattr(source, "__iter__"):
        return list(source)
    else:
        raise TypeError(f"Unsupported data source type: {type(source)}")


def load_crimes(
    source: Union[str, Path, List[Dict[str, Any]]],
    drop_invalid: bool = True,
    source_crs: Optional[Union[str, int]] = DEFAULT_CRS,
) -> List[Dict[str, Any]]:
    """Load, validate, and spatially prepare crime complaint records.

    Matches schema in docs/DATA_SCHEMA.md:
    - crime_id: str
    - crime_type: str
    - timestamp: ISO8601 string
    - amount: float (numeric)
    - latitude: float
    - longitude: float
    - location: {'lat': float, 'lng': float}
    - geometry: SpatialPoint(x=longitude, y=latitude, crs=source_crs)
    - crs: str (e.g. 'EPSG:4326')

    Args:
        source: File path (CSV/JSON) or list of crime dictionaries.
        drop_invalid: If True, skips records with missing/invalid coordinates or CRS.
                      If False, raises ValueError on first invalid record.
        source_crs: Expected CRS of source dataset (default: EPSG:4326).

    Returns:
        List of spatially prepared crime dictionaries.
    """
    validated_crs = validate_crs(source_crs if source_crs is not None else DEFAULT_CRS)
    raw_records = _load_raw_data(source)
    prepared_crimes: List[Dict[str, Any]] = []

    for idx, raw in enumerate(raw_records):
        prepared = prepare_spatial_record(raw, strict=not drop_invalid, crs=validated_crs)
        if prepared is None:
            continue

        # Cast amount to float if present and valid
        if "amount" in prepared and prepared["amount"] is not None and prepared["amount"] != "":
            try:
                prepared["amount"] = float(prepared["amount"])
            except (ValueError, TypeError):
                pass

        prepared_crimes.append(prepared)

    logger.info("Loaded %d valid crime records (from %d raw entries) with CRS %s.", len(prepared_crimes), len(raw_records), validated_crs)
    return prepared_crimes


def load_atms(
    source: Union[str, Path, List[Dict[str, Any]]],
    drop_invalid: bool = True,
    source_crs: Optional[Union[str, int]] = DEFAULT_CRS,
) -> List[Dict[str, Any]]:
    """Load, validate, and spatially prepare ATM records.

    Matches schema in docs/DATA_SCHEMA.md:
    - atm_id: str
    - bank: str
    - area: str
    - historical_risk_score: float or None
    - latitude: float
    - longitude: float
    - location: {'lat': float, 'lng': float}
    - geometry: SpatialPoint(x=longitude, y=latitude, crs=source_crs)
    - crs: str (e.g. 'EPSG:4326')

    Args:
        source: File path (CSV/JSON) or list of ATM dictionaries.
        drop_invalid: If True, skips records with missing/invalid coordinates or CRS.
                      If False, raises ValueError on first invalid record.
        source_crs: Expected CRS of source dataset (default: EPSG:4326).

    Returns:
        List of spatially prepared ATM dictionaries.
    """
    validated_crs = validate_crs(source_crs if source_crs is not None else DEFAULT_CRS)
    raw_records = _load_raw_data(source)
    prepared_atms: List[Dict[str, Any]] = []

    for idx, raw in enumerate(raw_records):
        prepared = prepare_spatial_record(raw, strict=not drop_invalid, crs=validated_crs)
        if prepared is None:
            continue

        # Cast historical_risk_score to float if present
        if "historical_risk_score" in prepared and prepared["historical_risk_score"] not in (None, ""):
            try:
                prepared["historical_risk_score"] = float(prepared["historical_risk_score"])
            except (ValueError, TypeError):
                pass

        prepared_atms.append(prepared)

    logger.info("Loaded %d valid ATM records (from %d raw entries) with CRS %s.", len(prepared_atms), len(raw_records), validated_crs)
    return prepared_atms
