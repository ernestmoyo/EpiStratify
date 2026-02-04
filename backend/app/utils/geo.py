"""GeoJSON helper utilities."""

import json
from typing import Any


def validate_geojson_geometry(geometry: dict) -> bool:
    """Validate basic GeoJSON geometry structure."""
    valid_types = {
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    }
    if not isinstance(geometry, dict):
        return False
    if geometry.get("type") not in valid_types:
        return False
    if "coordinates" not in geometry and geometry["type"] != "GeometryCollection":
        return False
    return True


def geojson_to_wkt(geojson: dict) -> str | None:
    """Convert GeoJSON geometry to WKT string using Shapely."""
    try:
        from shapely.geometry import shape

        geom = shape(geojson)
        return geom.wkt
    except Exception:
        return None
