from __future__ import annotations

import hashlib
import math
from typing import Any

from app.schemas.geo import (
    Coordinate,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    MapBounds,
    MapViewport,
    Place,
)


class NeshanPlaceNormalizer:
    @staticmethod
    def coordinate_from_location(data: dict[str, Any]) -> Coordinate:
        try:
            longitude = float(data["x"])
            latitude = float(data["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "مختصات معتبر در پاسخ سرویس نشان وجود ندارد."
            ) from exc

        return Coordinate(
            latitude=latitude,
            longitude=longitude,
        )

    def normalize_geocode(
        self,
        raw: dict[str, Any],
        address: str,
    ) -> Place:
        if str(raw.get("status", "")).upper() != "OK":
            raise ValueError("آدرس موردنظر توسط نشان پیدا نشد.")

        location = self.coordinate_from_location(
            raw.get("location") or {}
        )

        return Place(
            id=self._make_id(address, location),
            title=address,
            address=address,
            location=location,
            category="geocoded_address",
            metadata={
                "source": "neshan",
                "source_operation": "geocode",
                "status": raw.get("status"),
            },
        )

    def normalize_reverse(
        self,
        raw: dict[str, Any],
        location: Coordinate,
    ) -> Place:
        if str(raw.get("status", "")).upper() != "OK":
            raise ValueError("برای مختصات واردشده آدرسی پیدا نشد.")

        formatted_address = self._clean_text(
            raw.get("formatted_address")
        )

        title = (
            self._clean_text(raw.get("place"))
            or self._clean_text(raw.get("route_name"))
            or formatted_address
            or "موقعیت انتخاب‌شده"
        )

        return Place(
            id=self._make_id(title, location),
            title=title,
            address=formatted_address,
            location=location,
            category=(
                self._clean_text(raw.get("place_type"))
                or self._clean_text(raw.get("route_type"))
                or "address"
            ),
            region=self._clean_text(raw.get("state")),
            neighbourhood=self._clean_text(raw.get("neighbourhood")),
            metadata={
                "source": "neshan",
                "source_operation": "reverse_geocode",
                "city": self._clean_text(raw.get("city")),
                "county": self._clean_text(raw.get("county")),
                "district": self._clean_text(raw.get("district")),
                "village": self._clean_text(raw.get("village")),
                "municipality_zone": self._clean_text(
                    raw.get("municipality_zone")
                ),
                "route_name": self._clean_text(raw.get("route_name")),
                "route_type": self._clean_text(raw.get("route_type")),
                "in_traffic_zone": bool(
                    raw.get("in_traffic_zone", False)
                ),
                "in_odd_even_zone": bool(
                    raw.get("in_odd_even_zone", False)
                ),
            },
        )

    def normalize_search(
        self,
        raw: dict[str, Any],
        origin: Coordinate,
        limit: int = 10,
    ) -> list[Place]:
        places: list[Place] = []

        for item in raw.get("items") or []:
            if not isinstance(item, dict):
                continue

            try:
                location = self.coordinate_from_location(
                    item.get("location") or {}
                )
            except ValueError:
                continue

            title = self._clean_text(item.get("title"))
            if not title:
                continue

            distance = round(
                self.haversine_distance_meters(origin, location)
            )

            places.append(
                Place(
                    id=self._make_id(title, location),
                    title=title,
                    address=self._clean_text(item.get("address")),
                    location=location,
                    category=(
                        self._clean_text(item.get("type"))
                        or self._clean_text(item.get("category"))
                    ),
                    region=self._clean_text(item.get("region")),
                    neighbourhood=self._clean_text(
                        item.get("neighbourhood")
                    ),
                    distance_meters=distance,
                    metadata={
                        "source": "neshan",
                        "source_operation": "search",
                        "neshan_category": self._clean_text(
                            item.get("category")
                        ),
                    },
                )
            )

        places.sort(
            key=lambda place: (
                place.distance_meters
                if place.distance_meters is not None
                else float("inf")
            )
        )

        return places[: max(1, min(limit, 30))]

    def places_to_geojson(
        self,
        places: list[Place],
    ) -> GeoJSONFeatureCollection:
        features: list[GeoJSONFeature] = []

        for index, place in enumerate(places, start=1):
            features.append(
                GeoJSONFeature(
                    id=place.id,
                    geometry=GeoJSONGeometry(
                        type="Point",
                        coordinates=place.location.geojson_value,
                    ),
                    properties={
                        "id": place.id,
                        "rank": index,
                        "title": place.title,
                        "address": place.address,
                        "category": place.category,
                        "region": place.region,
                        "neighbourhood": place.neighbourhood,
                        "distance_meters": place.distance_meters,
                        "marker_type": "place",
                    },
                )
            )

        return GeoJSONFeatureCollection(features=features)

    def viewport_for_places(
        self,
        places: list[Place],
        fallback: Coordinate,
    ) -> MapViewport:
        if not places:
            return MapViewport(
                center=fallback,
                zoom=13,
            )

        if len(places) == 1:
            return MapViewport(
                center=places[0].location,
                zoom=15,
            )

        longitudes = [
            place.location.longitude
            for place in places
        ]
        latitudes = [
            place.location.latitude
            for place in places
        ]

        west = min(longitudes)
        east = max(longitudes)
        south = min(latitudes)
        north = max(latitudes)

        longitude_padding = max((east - west) * 0.12, 0.001)
        latitude_padding = max((north - south) * 0.12, 0.001)

        bounds = MapBounds(
            west=west - longitude_padding,
            south=south - latitude_padding,
            east=east + longitude_padding,
            north=north + latitude_padding,
        )

        center = Coordinate(
            latitude=(south + north) / 2,
            longitude=(west + east) / 2,
        )

        return MapViewport(
            center=center,
            zoom=13,
            bounds=bounds,
        )

    @staticmethod
    def haversine_distance_meters(
        origin: Coordinate,
        destination: Coordinate,
    ) -> float:
        earth_radius = 6_371_008.8

        latitude_1 = math.radians(origin.latitude)
        latitude_2 = math.radians(destination.latitude)

        delta_latitude = math.radians(
            destination.latitude - origin.latitude
        )
        delta_longitude = math.radians(
            destination.longitude - origin.longitude
        )

        a = (
            math.sin(delta_latitude / 2) ** 2
            + math.cos(latitude_1)
            * math.cos(latitude_2)
            * math.sin(delta_longitude / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return earth_radius * c

    @staticmethod
    def _make_id(
        title: str,
        location: Coordinate,
    ) -> str:
        value = (
            f"{title}|"
            f"{location.latitude:.7f}|"
            f"{location.longitude:.7f}"
        )

        digest = hashlib.sha1(
            value.encode("utf-8")
        ).hexdigest()[:16]

        return f"neshan-{digest}"

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        return text or None
