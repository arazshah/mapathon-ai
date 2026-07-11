from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Iterable

from app.schemas.geo import Coordinate, MapBounds, MapViewport


EARTH_RADIUS_METERS = 6_371_008.8


def haversine_distance(
    first: Coordinate,
    second: Coordinate,
) -> int:
    """
    Calculate the great-circle distance between two coordinates.

    The returned value is an approximate straight-line distance in meters,
    not the driving or walking distance.
    """
    lat1 = radians(first.latitude)
    lon1 = radians(first.longitude)
    lat2 = radians(second.latitude)
    lon2 = radians(second.longitude)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )

    distance = 2 * EARTH_RADIUS_METERS * asin(sqrt(value))
    return round(distance)


def build_viewport(
    coordinates: Iterable[Coordinate],
    *,
    default_zoom: float = 13,
) -> MapViewport | None:
    points = list(coordinates)

    if not points:
        return None

    latitudes = [point.latitude for point in points]
    longitudes = [point.longitude for point in points]

    south = min(latitudes)
    north = max(latitudes)
    west = min(longitudes)
    east = max(longitudes)

    center = Coordinate(
        latitude=(south + north) / 2,
        longitude=(west + east) / 2,
    )

    if len(points) == 1:
        return MapViewport(
            center=center,
            zoom=default_zoom,
            bounds=None,
        )

    lat_span = north - south
    lon_span = east - west
    span = max(lat_span, lon_span)

    if span < 0.005:
        zoom = 16
    elif span < 0.01:
        zoom = 15
    elif span < 0.03:
        zoom = 14
    elif span < 0.08:
        zoom = 13
    elif span < 0.2:
        zoom = 11
    elif span < 0.6:
        zoom = 9
    elif span < 2:
        zoom = 7
    else:
        zoom = 5

    return MapViewport(
        center=center,
        zoom=zoom,
        bounds=MapBounds(
            west=west,
            south=south,
            east=east,
            north=north,
        ),
    )
