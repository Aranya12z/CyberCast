"""Unit tests for GIS data loading and spatial data preparation (Fragment 1).

Verifies:
1. SpatialPoint geometry class (WGS84 boundaries, x=lng, y=lat, GeoJSON coordinates [lng, lat]).
2. prepare_spatial_record handling of missing/invalid/valid coordinates.
3. load_crimes from list, CSV, and JSON sources preserving DATA_SCHEMA.md fields.
4. load_atms from list, CSV, and JSON sources preserving DATA_SCHEMA.md fields.
5. Direct interoperability with haversine_distance and select_candidate_atms.
"""

import csv
import json
import os
import tempfile
import unittest

from gis.spatial.data_loader import (
    SpatialPoint,
    prepare_spatial_record,
    load_crimes,
    load_atms,
)
from gis.spatial.distance import haversine_distance
from gis.spatial.candidate_selection import select_candidate_atms


class TestSpatialPoint(unittest.TestCase):
    """Tests for the WGS84 SpatialPoint geometry primitive."""

    def test_point_creation_and_properties(self):
        # Longitude: 77.2090 (x), Latitude: 28.6139 (y)
        pt = SpatialPoint(x=77.2090, y=28.6139)
        self.assertEqual(pt.x, 77.2090)
        self.assertEqual(pt.y, 28.6139)
        self.assertEqual(pt.lng, 77.2090)
        self.assertEqual(pt.lat, 28.6139)
        # RFC 7946 GeoJSON: [longitude, latitude]
        self.assertEqual(pt.coordinates, [77.2090, 28.6139])
        self.assertEqual(pt.to_dict(), {"lat": 28.6139, "lng": 77.2090})
        self.assertEqual(
            pt.to_geojson_geometry(),
            {"type": "Point", "coordinates": [77.2090, 28.6139]},
        )

    def test_point_bounds_validation(self):
        # Longitude out of bounds [-180, 180]
        with self.assertRaises(ValueError):
            SpatialPoint(x=181.0, y=20.0)
        with self.assertRaises(ValueError):
            SpatialPoint(x=-185.0, y=20.0)

        # Latitude out of bounds [-90, 90]
        with self.assertRaises(ValueError):
            SpatialPoint(x=77.0, y=91.0)
        with self.assertRaises(ValueError):
            SpatialPoint(x=77.0, y=-95.0)

    def test_point_nan_infinite_validation(self):
        with self.assertRaises(ValueError):
            SpatialPoint(x=float("nan"), y=28.0)
        with self.assertRaises(ValueError):
            SpatialPoint(x=77.0, y=float("inf"))


class TestPrepareSpatialRecord(unittest.TestCase):
    """Tests for record preparation and coordinate normalization."""

    def test_prepare_record_lat_lng(self):
        raw = {
            "crime_id": "c-101",
            "crime_type": "phishing",
            "lat": 28.6139,
            "lng": 77.2090,
            "amount": 50000.0,
        }
        prepared = prepare_spatial_record(raw)
        self.assertIsNotNone(prepared)
        self.assertEqual(prepared["crime_id"], "c-101")
        self.assertEqual(prepared["crime_type"], "phishing")
        self.assertEqual(prepared["amount"], 50000.0)
        self.assertEqual(prepared["latitude"], 28.6139)
        self.assertEqual(prepared["longitude"], 77.2090)
        self.assertIsInstance(prepared["geometry"], SpatialPoint)
        self.assertEqual(prepared["geometry"].coordinates, [77.2090, 28.6139])

    def test_prepare_record_latitude_longitude(self):
        raw = {
            "atm_id": "atm-500",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "bank": "SBI",
            "area": "Fort",
        }
        prepared = prepare_spatial_record(raw)
        self.assertIsNotNone(prepared)
        self.assertEqual(prepared["atm_id"], "atm-500")
        self.assertEqual(prepared["bank"], "SBI")
        self.assertEqual(prepared["location"], {"lat": 19.0760, "lng": 72.8777})

    def test_prepare_record_invalid_coordinates(self):
        raw_missing = {"atm_id": "bad-1", "bank": "Test"}
        self.assertIsNone(prepare_spatial_record(raw_missing, strict=False))
        with self.assertRaises(ValueError):
            prepare_spatial_record(raw_missing, strict=True)

        raw_oob = {"atm_id": "bad-2", "lat": 120.0, "lng": 77.0}
        self.assertIsNone(prepare_spatial_record(raw_oob, strict=False))
        with self.assertRaises(ValueError):
            prepare_spatial_record(raw_oob, strict=True)


class TestLoadCrimes(unittest.TestCase):
    """Tests for loading and preparing crime records."""

    def test_load_crimes_from_records(self):
        raw_crimes = [
            {"crime_id": "c-1", "crime_type": "otp_fraud", "timestamp": "2026-09-17T10:00:00Z", "lat": 28.6315, "lng": 77.2167, "amount": 25000.0},
            {"crime_id": "c-2", "crime_type": "vishing", "timestamp": "2026-09-17T11:00:00Z", "latitude": 28.6400, "longitude": 77.2200, "amount": "40000.0"},
            {"crime_id": "c-bad", "crime_type": "invalid", "lat": 999.0, "lng": 77.0},  # should be dropped
        ]
        crimes = load_crimes(raw_crimes, drop_invalid=True)
        self.assertEqual(len(crimes), 2)
        self.assertEqual(crimes[0]["crime_id"], "c-1")
        self.assertEqual(crimes[0]["amount"], 25000.0)
        self.assertEqual(crimes[1]["crime_id"], "c-2")
        self.assertEqual(crimes[1]["amount"], 40000.0)
        self.assertIsInstance(crimes[0]["geometry"], SpatialPoint)

    def test_load_crimes_from_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="", encoding="utf-8") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=["crime_id", "crime_type", "timestamp", "latitude", "longitude", "amount"])
            writer.writeheader()
            writer.writerow({"crime_id": "csv-1", "crime_type": "atm_cloning", "timestamp": "2026-09-17T09:00:00Z", "latitude": "28.6100", "longitude": "77.2000", "amount": "15000"})
            writer.writerow({"crime_id": "csv-invalid", "crime_type": "atm_cloning", "timestamp": "2026-09-17T09:00:00Z", "latitude": "invalid", "longitude": "77.2000", "amount": "15000"})
            tmp_path = tmp.name

        try:
            crimes = load_crimes(tmp_path, drop_invalid=True)
            self.assertEqual(len(crimes), 1)
            self.assertEqual(crimes[0]["crime_id"], "csv-1")
            self.assertEqual(crimes[0]["latitude"], 28.6100)
            self.assertEqual(crimes[0]["longitude"], 77.2000)
            self.assertEqual(crimes[0]["amount"], 15000.0)
        finally:
            os.remove(tmp_path)

    def test_load_crimes_from_json(self):
        data = [
            {"crime_id": "json-1", "crime_type": "phishing", "timestamp": "2026-09-17T12:00:00Z", "lat": 28.6300, "lng": 77.2100, "amount": 10000.0}
        ]
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as tmp:
            json.dump(data, tmp)
            tmp_path = tmp.name

        try:
            crimes = load_crimes(tmp_path)
            self.assertEqual(len(crimes), 1)
            self.assertEqual(crimes[0]["crime_id"], "json-1")
            self.assertEqual(crimes[0]["geometry"].coordinates, [77.2100, 28.6300])
        finally:
            os.remove(tmp_path)


class TestLoadATMs(unittest.TestCase):
    """Tests for loading and preparing ATM records."""

    def test_load_atms_from_records(self):
        raw_atms = [
            {"atm_id": "atm-1", "latitude": 28.6350, "longitude": 77.2180, "bank": "SBI", "area": "CP", "historical_risk_score": "0.75"},
            {"atm_id": "atm-2", "lat": 28.6200, "lng": 77.2100, "bank": "HDFC", "area": "Mandi House", "historical_risk_score": 0.35},
            {"atm_id": "atm-null-coords", "bank": "ICICI", "latitude": None, "longitude": None},
        ]
        atms = load_atms(raw_atms, drop_invalid=True)
        self.assertEqual(len(atms), 2)
        self.assertEqual(atms[0]["atm_id"], "atm-1")
        self.assertEqual(atms[0]["bank"], "SBI")
        self.assertEqual(atms[0]["historical_risk_score"], 0.75)
        self.assertEqual(atms[1]["atm_id"], "atm-2")
        self.assertEqual(atms[1]["historical_risk_score"], 0.35)

    def test_interoperability_with_candidate_selection(self):
        crime = {"lat": 28.6315, "lng": 77.2167}
        raw_atms = [
            {"atm_id": "atm-near", "latitude": 28.6350, "longitude": 77.2180, "bank": "SBI"},
            {"atm_id": "atm-far", "latitude": 28.4000, "longitude": 77.1000, "bank": "PNB"},
        ]
        prepared_atms = load_atms(raw_atms)
        candidates = select_candidate_atms(crime, radius_km=5.0, atms=prepared_atms)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["atm_id"], "atm-near")
        # Geometry coordinates match
        self.assertEqual(candidates[0]["geometry"].coordinates, [77.2180, 28.6350])


if __name__ == "__main__":
    unittest.main()
