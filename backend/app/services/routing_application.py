from __future__ import annotations

from typing import Any

from app.clients.neshan.routing import NeshanRoutingService
from app.schemas.geo import (
    Coordinate,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    MapBounds,
    MapViewport,
    Place,
    RouteResult,
    RouteStep,
)
from app.services.polyline_decoder import decode_polyline


class RoutingApplicationService:
    def __init__(
        self,
        neshan: NeshanRoutingService,
    ) -> None:
        self.neshan = neshan

    async def route(
        self,
        *,
        origin: Coordinate,
        destination: Coordinate,
        origin_title: str = "مبدأ",
        destination_title: str = "مقصد",
        vehicle_type: str = "car",
        alternatives: bool = True,
        avoid_traffic_zone: bool = False,
        avoid_odd_even_zone: bool = False,
    ) -> dict[str, Any]:
        raw = await self.neshan.route(
            origin=origin,
            destination=destination,
            vehicle_type=vehicle_type,
            alternatives=alternatives,
            avoid_traffic_zone=avoid_traffic_zone,
            avoid_odd_even_zone=avoid_odd_even_zone,
        )

        routes = self._normalize_routes(
            raw=raw,
            vehicle_type=vehicle_type,
        )

        places = [
            Place(
                id="route-origin",
                title=origin_title,
                location=origin,
                category="route_origin",
            ),
            Place(
                id="route-destination",
                title=destination_title,
                location=destination,
                category="route_destination",
            ),
        ]

        geojson = self._build_geojson(
            routes=routes,
            origin=origin,
            destination=destination,
            origin_title=origin_title,
            destination_title=destination_title,
        )

        viewport = self._build_viewport(
            routes=routes,
            origin=origin,
            destination=destination,
        )

        if routes:
            primary_route = routes[0]

            message = (
                f"مسیر از «{origin_title}» تا «{destination_title}» "
                f"با طول تقریبی "
                f"{self._format_distance(primary_route.distance_meters)} "
                f"و زمان تقریبی "
                f"{self._format_duration(primary_route.duration_seconds)} "
                "پیدا شد."
            )

            metrics = {
                "distance_meters": primary_route.distance_meters,
                "duration_seconds": primary_route.duration_seconds,
                "total_places": len(places),
                "extra": {
                    "route_count": len(routes),
                    "alternative_count": max(0, len(routes) - 1),
                    "vehicle_type": vehicle_type,
                },
            }
        else:
            message = (
                f"مسیری از «{origin_title}» تا "
                f"«{destination_title}» پیدا نشد."
            )

            metrics = {
                "total_places": len(places),
                "extra": {
                    "route_count": 0,
                    "alternative_count": 0,
                    "vehicle_type": vehicle_type,
                },
            }

        return {
            "operation": "route",
            "message": message,
            "map": viewport.model_dump(mode="json"),
            "geojson": geojson.model_dump(mode="json"),
            "places": [
                place.model_dump(mode="json")
                for place in places
            ],
            "routes": [
                route.model_dump(mode="json")
                for route in routes
            ],
            "metrics": metrics,
            "warnings": [] if routes else [
                "سرویس نشان مسیری برای این مبدأ و مقصد برنگرداند."
            ],
        }

    def _normalize_routes(
        self,
        *,
        raw: dict[str, Any],
        vehicle_type: str,
    ) -> list[RouteResult]:
        raw_routes = raw.get("routes")

        if not isinstance(raw_routes, list):
            return []

        normalized: list[RouteResult] = []

        for route_index, raw_route in enumerate(raw_routes, start=1):
            if not isinstance(raw_route, dict):
                continue

            coordinates = self._route_coordinates(raw_route)

            if len(coordinates) < 2:
                continue

            legs = raw_route.get("legs")

            if not isinstance(legs, list):
                legs = []

            distance_meters = 0
            duration_seconds = 0
            steps: list[RouteStep] = []
            summaries: list[str] = []

            for leg in legs:
                if not isinstance(leg, dict):
                    continue

                distance_meters += self._metric_value(
                    leg.get("distance")
                )
                duration_seconds += self._metric_value(
                    leg.get("duration")
                )

                summary = leg.get("summary")

                if isinstance(summary, str) and summary.strip():
                    summaries.append(summary.strip())

                raw_steps = leg.get("steps")

                if not isinstance(raw_steps, list):
                    continue

                for raw_step in raw_steps:
                    if not isinstance(raw_step, dict):
                        continue

                    steps.append(
                        RouteStep(
                            instruction=self._optional_string(
                                raw_step.get("instruction")
                            ),
                            name=self._optional_string(
                                raw_step.get("name")
                            ),
                            distance_meters=self._metric_value_or_none(
                                raw_step.get("distance")
                            ),
                            duration_seconds=self._metric_value_or_none(
                                raw_step.get("duration")
                            ),
                        )
                    )

            title = (
                "مسیر پیشنهادی"
                if route_index == 1
                else f"مسیر جایگزین {route_index - 1}"
            )

            normalized.append(
                RouteResult(
                    id=f"route-{route_index}",
                    title=title,
                    distance_meters=max(0, distance_meters),
                    duration_seconds=max(0, duration_seconds),
                    geometry=GeoJSONGeometry(
                        type="LineString",
                        coordinates=coordinates,
                    ),
                    steps=steps,
                    metadata={
                        "route_index": route_index,
                        "is_primary": route_index == 1,
                        "is_alternative": route_index > 1,
                        "vehicle_type": vehicle_type,
                        "summary": "، ".join(summaries) or None,
                    },
                )
            )

        return normalized

    @staticmethod
    def _route_coordinates(
        raw_route: dict[str, Any],
    ) -> list[list[float]]:
        overview = raw_route.get("overview_polyline")

        if isinstance(overview, dict):
            encoded = overview.get("points")
        elif isinstance(overview, str):
            encoded = overview
        else:
            encoded = None

        if not isinstance(encoded, str) or not encoded:
            return []

        return decode_polyline(encoded)

    @staticmethod
    def _metric_value(value: Any) -> int:
        metric = RoutingApplicationService._metric_value_or_none(
            value
        )
        return metric or 0

    @staticmethod
    def _metric_value_or_none(value: Any) -> int | None:
        if isinstance(value, dict):
            value = value.get("value")

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return max(0, int(round(value)))

        if isinstance(value, str):
            try:
                return max(0, int(round(float(value))))
            except ValueError:
                return None

        return None

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()

        return None

    @staticmethod
    def _build_geojson(
        *,
        routes: list[RouteResult],
        origin: Coordinate,
        destination: Coordinate,
        origin_title: str,
        destination_title: str,
    ) -> GeoJSONFeatureCollection:
        features: list[GeoJSONFeature] = []

        for index, route in enumerate(routes):
            features.append(
                GeoJSONFeature(
                    id=route.id,
                    geometry=route.geometry,
                    properties={
                        "kind": "route",
                        "title": route.title,
                        "distance_meters": route.distance_meters,
                        "duration_seconds": route.duration_seconds,
                        "is_primary": index == 0,
                        "route_index": index + 1,
                    },
                )
            )

        features.extend(
            [
                GeoJSONFeature(
                    id="route-origin",
                    geometry=GeoJSONGeometry(
                        type="Point",
                        coordinates=origin.geojson_value,
                    ),
                    properties={
                        "kind": "route_origin",
                        "title": origin_title,
                        "marker": "origin",
                    },
                ),
                GeoJSONFeature(
                    id="route-destination",
                    geometry=GeoJSONGeometry(
                        type="Point",
                        coordinates=destination.geojson_value,
                    ),
                    properties={
                        "kind": "route_destination",
                        "title": destination_title,
                        "marker": "destination",
                    },
                ),
            ]
        )

        return GeoJSONFeatureCollection(features=features)

    @staticmethod
    def _build_viewport(
        *,
        routes: list[RouteResult],
        origin: Coordinate,
        destination: Coordinate,
    ) -> MapViewport:
        coordinates: list[list[float]] = [
            origin.geojson_value,
            destination.geojson_value,
        ]

        for route in routes:
            route_coordinates = route.geometry.coordinates

            if isinstance(route_coordinates, list):
                for coordinate in route_coordinates:
                    if (
                        isinstance(coordinate, list)
                        and len(coordinate) >= 2
                        and isinstance(coordinate[0], (int, float))
                        and isinstance(coordinate[1], (int, float))
                    ):
                        coordinates.append(
                            [
                                float(coordinate[0]),
                                float(coordinate[1]),
                            ]
                        )

        longitudes = [coordinate[0] for coordinate in coordinates]
        latitudes = [coordinate[1] for coordinate in coordinates]

        west = min(longitudes)
        east = max(longitudes)
        south = min(latitudes)
        north = max(latitudes)

        longitude_padding = max((east - west) * 0.08, 0.002)
        latitude_padding = max((north - south) * 0.08, 0.002)

        bounds = MapBounds(
            west=max(-180, west - longitude_padding),
            south=max(-90, south - latitude_padding),
            east=min(180, east + longitude_padding),
            north=min(90, north + latitude_padding),
        )

        center = Coordinate(
            latitude=(south + north) / 2,
            longitude=(west + east) / 2,
        )

        span = max(east - west, north - south)

        if span < 0.01:
            zoom = 15
        elif span < 0.03:
            zoom = 13
        elif span < 0.08:
            zoom = 12
        elif span < 0.2:
            zoom = 10
        elif span < 0.5:
            zoom = 9
        elif span < 1:
            zoom = 8
        else:
            zoom = 6

        return MapViewport(
            center=center,
            zoom=zoom,
            bounds=bounds,
        )

    @staticmethod
    def _format_distance(distance_meters: int) -> str:
        if distance_meters < 1000:
            return f"{distance_meters} متر"

        kilometers = distance_meters / 1000

        if kilometers.is_integer():
            return f"{int(kilometers)} کیلومتر"

        return f"{kilometers:.1f} کیلومتر"

    @staticmethod
    def _format_duration(duration_seconds: int) -> str:
        minutes = max(1, round(duration_seconds / 60))

        if minutes < 60:
            return f"{minutes} دقیقه"

        hours, remaining_minutes = divmod(minutes, 60)

        if remaining_minutes == 0:
            return f"{hours} ساعت"

        return f"{hours} ساعت و {remaining_minutes} دقیقه"
