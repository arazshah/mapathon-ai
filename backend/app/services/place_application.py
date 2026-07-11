from __future__ import annotations

import math
from typing import Any

from app.clients.neshan.places import NeshanPlacesService
from app.schemas.geo import (
    Coordinate,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    Place,
)
from app.services.place_normalizer import NeshanPlaceNormalizer


class PlaceApplicationService:
    def __init__(
        self,
        neshan: NeshanPlacesService,
        normalizer: NeshanPlaceNormalizer | None = None,
    ) -> None:
        self.neshan = neshan
        self.normalizer = normalizer or NeshanPlaceNormalizer()

    async def geocode(
        self,
        address: str,
    ) -> dict[str, Any]:
        raw = await self.neshan.geocode(address)
        place = self.normalizer.normalize_geocode(raw, address)

        return self._build_payload(
            operation="geocode",
            message=f"موقعیت «{address}» پیدا شد.",
            places=[place],
            fallback=place.location,
        )

    async def reverse_geocode(
        self,
        location: Coordinate,
    ) -> dict[str, Any]:
        raw = await self.neshan.reverse_geocode(location)
        place = self.normalizer.normalize_reverse(raw, location)

        return self._build_payload(
            operation="reverse_geocode",
            message=(
                f"آدرس این موقعیت «"
                f"{place.address or place.title}» است."
            ),
            places=[place],
            fallback=location,
        )

    async def search(
        self,
        term: str,
        location: Coordinate,
        limit: int = 10,
    ) -> dict[str, Any]:
        raw = await self.neshan.search(term, location)

        places = self.normalizer.normalize_search(
            raw=raw,
            origin=location,
            limit=limit,
        )

        if places:
            message = (
                f"{len(places)} نتیجه برای «{term}» "
                "در نزدیکی موقعیت موردنظر پیدا شد."
            )
        else:
            message = (
                f"نتیجه‌ای برای «{term}» "
                "در نزدیکی موقعیت موردنظر پیدا نشد."
            )

        payload = self._build_payload(
            operation="search",
            message=message,
            places=places,
            fallback=location,
        )

        payload["metrics"] = {
            "total_places": len(places),
            "nearest_distance_meters": (
                places[0].distance_meters
                if places
                else None
            ),
        }

        return payload

    async def search_along_route(
        self,
        *,
        term: str,
        route_coordinates: list[list[float]],
        radius_meters: int = 500,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Search a generic term around sampled points of a route.

        route_coordinates use GeoJSON order:
        [longitude, latitude].
        """
        if len(route_coordinates) < 2:
            return {
                "operation": "search_along_route",
                "message": "هندسه معتبر برای مسیر وجود ندارد.",
                "places": [],
                "routes": [],
                "geojson": {
                    "type": "FeatureCollection",
                    "features": [],
                },
                "metrics": {
                    "total_places": 0,
                },
                "warnings": [
                    "مسیر قابل استفاده برای جستجو پیدا نشد."
                ],
            }

        safe_limit = max(1, min(limit, 30))
        safe_radius = max(100, min(radius_meters, 3000))

        sample_count = min(
            8,
            max(2, math.ceil(len(route_coordinates) / 40)),
        )

        sampled = self._sample_route(
            route_coordinates,
            sample_count,
        )

        unique_places: dict[str, Place] = {}

        for longitude, latitude in sampled:
            payload = await self.search(
                term=term,
                location=Coordinate(
                    latitude=latitude,
                    longitude=longitude,
                ),
                limit=min(10, safe_limit * 2),
            )

            for place_data in payload.get("places") or []:
                try:
                    place = Place.model_validate(place_data)
                except Exception:
                    continue

                distance_to_route = (
                    self._distance_to_route_meters(
                        place.location,
                        route_coordinates,
                    )
                )

                if distance_to_route > safe_radius:
                    continue

                metadata = dict(place.metadata)
                metadata.update(
                    {
                        "source_operation": (
                            "search_along_route"
                        ),
                        "route_distance_meters": round(
                            distance_to_route
                        ),
                        "search_term": term,
                    }
                )

                place = place.model_copy(
                    update={
                        "distance_meters": round(
                            distance_to_route
                        ),
                        "metadata": metadata,
                    }
                )

                unique_places[place.id or self._place_key(place)] = place

        places = sorted(
            unique_places.values(),
            key=lambda item: (
                item.distance_meters
                if item.distance_meters is not None
                else float("inf")
            ),
        )[:safe_limit]

        features = [
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
                    "distance_meters": place.distance_meters,
                    "route_distance_meters": place.metadata.get(
                        "route_distance_meters"
                    ),
                    "marker_type": "place",
                    "search_term": term,
                },
            )
            for index, place in enumerate(places, start=1)
        ]

        return {
            "operation": "search_along_route",
            "message": (
                f"{len(places)} نتیجه برای «{term}» "
                "در نزدیکی مسیر پیدا شد."
                if places
                else (
                    f"نتیجه‌ای برای «{term}» "
                    "در نزدیکی مسیر پیدا نشد."
                )
            ),
            "places": [
                place.model_dump(mode="json")
                for place in places
            ],
            "routes": [],
            "geojson": GeoJSONFeatureCollection(
                features=features
            ).model_dump(mode="json"),
            "metrics": {
                "total_places": len(places),
                "search_radius_meters": safe_radius,
                "sampled_route_points": len(sampled),
            },
            "warnings": [],
        }

    def _build_payload(
        self,
        operation: str,
        message: str,
        places: list[Place],
        fallback: Coordinate,
    ) -> dict[str, Any]:
        viewport = self.normalizer.viewport_for_places(
            places=places,
            fallback=fallback,
        )

        geojson = self.normalizer.places_to_geojson(places)

        return {
            "operation": operation,
            "message": message,
            "map": viewport.model_dump(mode="json"),
            "geojson": geojson.model_dump(mode="json"),
            "places": [
                place.model_dump(mode="json")
                for place in places
            ],
            "routes": [],
            "metrics": {
                "total_places": len(places),
            },
        }

    @staticmethod
    def _sample_route(
        coordinates: list[list[float]],
        count: int,
    ) -> list[list[float]]:
        if count >= len(coordinates):
            return coordinates

        indexes = {
            round(index * (len(coordinates) - 1) / (count - 1))
            for index in range(count)
        }

        return [coordinates[index] for index in sorted(indexes)]

    @classmethod
    def _distance_to_route_meters(
        cls,
        place: Coordinate,
        route: list[list[float]],
    ) -> float:
        best = float("inf")

        for first, second in zip(route, route[1:]):
            if len(first) < 2 or len(second) < 2:
                continue

            distance = cls._distance_to_segment_meters(
                place,
                first,
                second,
            )

            best = min(best, distance)

        return best

    @staticmethod
    def _distance_to_segment_meters(
        point: Coordinate,
        first: list[float],
        second: list[float],
    ) -> float:
        earth_radius = 6_371_008.8
        latitude = math.radians(point.latitude)

        scale_x = earth_radius * math.cos(latitude)
        scale_y = earth_radius

        px = math.radians(point.longitude) * scale_x
        py = math.radians(point.latitude) * scale_y

        ax = math.radians(first[0]) * scale_x
        ay = math.radians(first[1]) * scale_y
        bx = math.radians(second[0]) * scale_x
        by = math.radians(second[1]) * scale_y

        dx = bx - ax
        dy = by - ay

        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)

        ratio = (
            ((px - ax) * dx + (py - ay) * dy)
            / (dx * dx + dy * dy)
        )

        ratio = max(0.0, min(1.0, ratio))

        closest_x = ax + ratio * dx
        closest_y = ay + ratio * dy

        return math.hypot(
            px - closest_x,
            py - closest_y,
        )

    @staticmethod
    def _place_key(place: Place) -> str:
        return (
            f"{place.title}|"
            f"{place.location.latitude:.6f}|"
            f"{place.location.longitude:.6f}"
        )
