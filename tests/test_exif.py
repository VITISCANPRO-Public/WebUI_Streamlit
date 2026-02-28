"""
Tests for get_exif_data() in app.py.

What is tested and why:
- get_exif_data() contains the only real business logic in the app:
  a DMS (degrees/minutes/seconds) → decimal degrees conversion.
  If this math is wrong, every parcel map is plotted at the wrong location.
- The function also parses a date string from EXIF metadata —
  a malformed date must not crash the app.
- Images without EXIF data are common (screenshots, WhatsApp photos) —
  the function must return safe defaults instead of raising an exception.

PIL EXIF tag numbers used:
  34853 → "GPSInfo"          (GPS coordinate block)
  36867 → "DateTimeOriginal" (capture timestamp)

GPS sub-keys inside the GPSInfo block:
  value[2] → (degrees, minutes, seconds) for latitude
  value[4] → (degrees, minutes, seconds) for longitude
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


# ─── Import helper ────────────────────────────────────────────────────────────
# app.py uses Streamlit at the module level (decorators, session_state).
# We mock the entire streamlit module before importing to avoid
# needing a running Streamlit server during tests.

import sys
sys.modules.setdefault("streamlit", MagicMock())
sys.modules.setdefault("streamlit_folium", MagicMock())
sys.modules.setdefault("folium", MagicMock())

from app import get_exif_data  # noqa: E402


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_image_file(exif_dict: dict | None = None) -> io.BytesIO:
    """
    Creates an in-memory JPEG image file, optionally embedding EXIF data.

    PIL's _getexif() is the legacy method used by app.py to read EXIF.
    We patch it directly on the Image instance to inject controlled test data
    without needing real camera files.
    """
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _patch_exif(image_file: io.BytesIO, exif_dict: dict | None):
    """
    Patches PIL.Image.open so that the returned Image object reports
    the given exif_dict when _getexif() is called.

    Returns the patch context manager — use as:
        with _patch_exif(file, data) as mock_open:
            ...
    """
    mock_img = MagicMock()
    mock_img._getexif.return_value = exif_dict

    return patch("PIL.Image.open", return_value=mock_img)


# ─── Constants ────────────────────────────────────────────────────────────────

# EXIF tag numbers (from PIL.ExifTags.TAGS)
TAG_GPS_INFO          = 34853
TAG_DATE_TIME_ORIGINAL = 36867

# Reference point: Paris, France
# 48°51'30" N  →  48 + 51/60 + 30/3600 = 48.858333...
# 2°21'05" E   →  2  + 21/60 + 5/3600  =  2.351388...
PARIS_LAT_DMS = (48, 51, 30)
PARIS_LON_DMS = (2,  21,  5)
PARIS_LAT_DEC = 48 + 51 / 60 + 30 / 3600   # 48.858333...
PARIS_LON_DEC =  2 + 21 / 60 +  5 / 3600   #  2.351388...


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestGetExifDataDefaults:
    """Image without any EXIF data must return safe defaults, never raise."""

    def test_no_exif_returns_zero_coordinates(self):
        """An image with no EXIF block returns lon=0.0 and lat=0.0."""
        f = _make_image_file()
        with _patch_exif(f, exif_dict=None):
            lon, lat, _ = get_exif_data(f)
        assert lon == 0.0
        assert lat == 0.0

    def test_no_exif_returns_string_date(self):
        """Date returned when no EXIF is present must be a non-empty string."""
        f = _make_image_file()
        with _patch_exif(f, exif_dict=None):
            _, _, date = get_exif_data(f)
        assert isinstance(date, str)
        assert len(date) > 0

    def test_empty_exif_dict_returns_defaults(self):
        """An empty EXIF dict (no tags) returns the same safe defaults."""
        f = _make_image_file()
        with _patch_exif(f, exif_dict={}):
            lon, lat, _ = get_exif_data(f)
        assert lon == 0.0
        assert lat == 0.0

    def test_corrupt_image_does_not_raise(self):
        """
        If PIL.Image.open raises (corrupt file, wrong format),
        get_exif_data must catch it and return defaults silently.
        This is the outer try/except in the function.
        """
        f = io.BytesIO(b"this is not an image")
        lon, lat, date = get_exif_data(f)
        assert lon == 0.0
        assert lat == 0.0
        assert isinstance(date, str)


class TestDmsToDecimalConversion:
    """
    Core math: DMS (degrees / minutes / seconds) → decimal degrees.

    Formula: decimal = degrees + minutes/60 + seconds/3600
    This is the only mathematical logic in the entire Streamlit app.
    A wrong result here means every parcel is mapped at the wrong location.
    """

    def test_paris_latitude_conversion(self):
        """48°51'30" N → 48.858333..."""
        exif = {TAG_GPS_INFO: {2: PARIS_LAT_DMS, 4: PARIS_LON_DMS}}
        f = _make_image_file()
        with _patch_exif(f, exif):
            _, lat, _ = get_exif_data(f)
        assert lat == pytest.approx(PARIS_LAT_DEC, abs=1e-6)

    def test_paris_longitude_conversion(self):
        """2°21'05" E → 2.351388..."""
        exif = {TAG_GPS_INFO: {2: PARIS_LAT_DMS, 4: PARIS_LON_DMS}}
        f = _make_image_file()
        with _patch_exif(f, exif):
            lon, _, _ = get_exif_data(f)
        assert lon == pytest.approx(PARIS_LON_DEC, abs=1e-6)

    def test_zero_minutes_and_seconds(self):
        """Whole-degree coordinates: 45°00'00" → 45.0 exactly."""
        exif = {TAG_GPS_INFO: {2: (45, 0, 0), 4: (10, 0, 0)}}
        f = _make_image_file()
        with _patch_exif(f, exif):
            lon, lat, _ = get_exif_data(f)
        assert lat == pytest.approx(45.0, abs=1e-9)
        assert lon == pytest.approx(10.0, abs=1e-9)

    def test_max_minutes_and_seconds(self):
        """
        Edge case: 59 minutes and 59 seconds.
        Result must be strictly less than the next whole degree.
        """
        exif = {TAG_GPS_INFO: {2: (10, 59, 59), 4: (20, 59, 59)}}
        f = _make_image_file()
        with _patch_exif(f, exif):
            lon, lat, _ = get_exif_data(f)
        assert lat < 11.0
        assert lon < 21.0
        assert lat > 10.9
        assert lon > 20.9

    def test_equator_coordinates(self):
        """0°00'00" → 0.0 — equator / prime meridian intersection."""
        exif = {TAG_GPS_INFO: {2: (0, 0, 0), 4: (0, 0, 0)}}
        f = _make_image_file()
        with _patch_exif(f, exif):
            lon, lat, _ = get_exif_data(f)
        assert lat == pytest.approx(0.0, abs=1e-9)
        assert lon == pytest.approx(0.0, abs=1e-9)


class TestDateParsing:
    """EXIF DateTimeOriginal parsing."""

    def test_valid_date_is_parsed_correctly(self):
        """
        EXIF date format is "YYYY:MM:DD HH:MM:SS".
        The function reformats it to "YYYY-MM-DD HH:MM:SS".
        """
        exif = {TAG_DATE_TIME_ORIGINAL: "2024:06:15 10:30:00"}
        f = _make_image_file()
        with _patch_exif(f, exif):
            _, _, date = get_exif_data(f)
        assert date == "2024-06-15 10:30:00"

    def test_invalid_date_does_not_crash(self):
        """
        A malformed date string in EXIF must not raise an exception.
        The function must fall back to the default date string.
        """
        exif = {TAG_DATE_TIME_ORIGINAL: "not-a-date"}
        f = _make_image_file()
        with _patch_exif(f, exif):
            _, _, date = get_exif_data(f)
        assert isinstance(date, str)
        assert len(date) > 0

    def test_gps_and_date_together(self):
        """Both GPS coordinates and date are extracted correctly in the same image."""
        exif = {
            TAG_GPS_INFO: {2: PARIS_LAT_DMS, 4: PARIS_LON_DMS},
            TAG_DATE_TIME_ORIGINAL: "2024:07:20 08:15:00"
        }
        f = _make_image_file()
        with _patch_exif(f, exif):
            lon, lat, date = get_exif_data(f)
        assert lat == pytest.approx(PARIS_LAT_DEC, abs=1e-6)
        assert lon == pytest.approx(PARIS_LON_DEC, abs=1e-6)
        assert date == "2024-07-20 08:15:00"

    def test_gps_without_date_uses_default(self):
        """Image with GPS but no DateTimeOriginal tag returns a valid default date."""
        exif = {TAG_GPS_INFO: {2: PARIS_LAT_DMS, 4: PARIS_LON_DMS}}
        f = _make_image_file()
        with _patch_exif(f, exif):
            _, _, date = get_exif_data(f)
        assert isinstance(date, str)
        assert len(date) > 0