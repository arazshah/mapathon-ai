from __future__ import annotations

from typing import Any

from app.schemas.geo import (
    Coordinate,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    Place,
    RouteResult,
    RouteStep,
)
from app.schemas.query import (
    OperationType,
    QueryMetrics,
    QueryResponse,
)
from app.services.geo_utils import build_viewport, haversine_distance
from app.services.polyline_decoder import (
    decode_polyline,
    find_encoded_polyline,
)


class NeshanNormalizer:
    @staticmethod
    def normalize_geocode(
        raw: dict[str, Any],
        *,
        query: str,
    ) -> QueryResponse:
        location = NeshanNormalizer._coordinate_from_location(
            raw.get("location")
        )

        if location is None:
            return QueryResponse(
                success=False,
                query=query,
                operation=OperationType.geocode,
                message="مختصات معتبری برای این آدرس پیدا نشد.",
                warnings=["پاسخ Geocoding فاقد location معتبر بود."],
            )

        place = Place(
            title=query,
            address=query,
            location=location,
            category="geocoded_location",
            metadata={
                "provider": "neshan",
                "status": raw.get("status"),
            },
        )

        feature = NeshanNormalizer._place_feature(
            place,
            feature_id="geocode-result",
        )

        return QueryResponse(
            success=True,
            query=query,
            operation=OperationType.geocode,
            message=f"موقعیت «{query}» پیدا شد.",
            map=build_viewport([location], default_zoom=16),
            geojson=GeoJSONFeatureCollection(features=[feature]),
            places=[place],
            metrics=QueryMetrics(total_places=1),
            tools_used=["neshan_geocode"],
        )

    @staticmethod
    def normalize_reverse_geocode(
        raw: dict[str, Any],
        *,
        location: Coordinate,
    ) -> QueryResponse:
        formatted_address = (
            raw.get("formatted_address")
            or raw.get("place")
            or raw.get("route_name")
            or "آدرس نامشخص"
        )

        place = Place(
            title=formatted_address,
            address=formatted_address,
            location=location,
            category=raw.get("place_type") or raw.get("route_type"),
            region=raw.get("state"),
            neighbourhood=raw.get("neighbourhood"),
            metadata={
                "provider": "neshan",
                "status": raw.get("status"),
                "city": raw.get("city"),
                "state": raw.get("state"),
                "county": raw.get("county"),
                "district": raw.get("district"),
                "village": raw.get("village"),
                "route_name": raw.get("route_name"),
                "route_type": raw.get("route_type"),
                "municipality_zone": raw.get("municipality_zone"),
                "in_traffic_zone": raw.get("in_traffic_zone"),
                "in_odd_even_zone": raw.get("in_odd_even_zone"),
            },
        )

        feature = NeshanNormalizer._place_feature(
            place,
            feature_id="reverse-geocode-result",
        )

        return QueryResponse(
            success=True,
            query=f"{location.latitude},{location.longitude}",
            operation=OperationType.reverse_geocode,
            message=formatted_address,
            map=build_viewport([location], default_zoom=17),
            geojson=GeoJSONFeatureCollection(features=[feature]),
            places=[place],
            metrics=QueryMetrics(total_places=1),
            tools_used=["neshan_reverse_geocode"],
        )

    @staticmethod
    def normalize_search(
        raw: dict[str, Any],
        *,
        term: str,
        origin: Coordinate,
        limit: int = 20,
    ) -> QueryResponse:
        raw_items = raw.get("items")

        if not isinstance(raw_items, list):
            raw_items = []

        places: list[Place] = []

        for index, item in enumerate(raw_items):
            if not isinstance(item, dict):
                continue

            location = NeshanNormalizer._coordinate_from_location(
                item.get("location")
            )

            if location is None:
                continue

            distance = haversine_distance(origin, location)

            place = Place(
                id=str(index + 1),
                title=item.get("title") or "مکان بدون نام",
                address=item.get("address"),
                location=location,
                category=item.get("type") or item.get("category"),
                region=item.get("region"),
                neighbourhood=item.get("neighbourhood"),
                distance_meters=distance,
                metadata={
                    "provider": "neshan",
                    "source_category": item.get("category"),
                    "source_type": item.get("type"),
                },
            )

            places.append(place)

        places.sort(
            key=lambda place: (
                place.distance_meters
                if place.distance_meters is not None
                else float("inf")
            )
        )

        places = places[:limit]

        features = [
            NeshanNormalizer._place_feature(
                place,
                feature_id=place.id or str(index + 1),
            )
            for index, place in enumerate(places)
        ]

        coordinates = [origin, *[place.location for place in places]]

        if not places:
            message = f"نتیجه‌ای برای «{term}» در اطراف این موقعیت پیدا نشد."
        else:
            message = (
                f"{len(places)} نتیجه نزدیک برای «{term}» پیدا شد."
            )

        return QueryResponse(
            success=bool(places),
            query=term,
            operation=OperationType.search,
            message=message,
            map=build_viewport(coordinates, default_zoom=14),
            geojson=GeoJSONFeatureCollection(features=features),
            places=places,
            metrics=QueryMetrics(
                total_places=len(places),
                extra={
                    "provider_count": raw.get(
                        "count",
                        len(raw_items),
                    ),
                    "distance_type": "straight_line",
                    "search_origin": {
                        "latitude": origin.latitude,
                        "longitude": origin.longitude,
                    },
                },
            ),
            tools_used=["neshan_search"],
        )

    @staticmethod
    def normalize_route(
        raw: dict[str, Any],
        *,
        origin: Coordinate,
        destination: Coordinate,
        operation: OperationType = OperationType.route,
    ) -> QueryResponse:
        raw_routes = raw.get("routes")

        if not isinstance(raw_routes, list):
            raw_routes = []

        routes: list[RouteResult] = []
        route_features: list[GeoJSONFeature] = []
        warnings: list[str] = []

        for route_index, raw_route in enumerate(raw_routes):
            if not isinstance(raw_route, dict):
                continue

            legs = raw_route.get("legs")
            if not isinstance(legs, list):
                legs = []

            distance_meters = 0
            duration_seconds = 0
            steps: list[RouteStep] = []

            for leg in legs:
                if not isinstance(leg, dict):
                    continue

                distance_meters += NeshanNormalizer._numeric_value(
                    leg.get("distance")
                )
                duration_seconds += NeshanNormalizer._numeric_value(
                    leg.get("duration")
                )

                raw_steps = leg.get("steps")

                if not isinstance(raw_steps, list):
                    continue

                for raw_step in raw_steps:
                    if not isinstance(raw_step, dict):
                        continue

                    steps.append(
                        RouteStep(
                            instruction=raw_step.get("instruction"),
                            name=raw_step.get("name"),
                            distance_meters=(
                                NeshanNormalizer._numeric_value(
                                    raw_step.get("distance")
                                )
                            ),
                            duration_seconds=(
                                NeshanNormalizer._numeric_value(
                                    raw_step.get("duration")
                                )
                            ),
                        )
                    )

            if distance_meters == 0:
                distance_meters = NeshanNormalizer._numeric_value(
                    raw_route.get("distance")
                )

            if duration_seconds == 0:
                duration_seconds = NeshanNormalizer._numeric_value(
                    raw_route.get("duration")
                )

            encoded_polyline = find_encoded_polyline(raw_route)

            if encoded_polyline is None:
                warnings.append(
                    f"هندسه مسیر شماره {route_index + 1} پیدا نشد."
                )
                continue

            try:
                geometry = decode_polyline(encoded_polyline)
            except ValueError:
                warnings.append(
                    f"Polyline مسیر شماره {route_index + 1} معتبر نبود."
                )
                continue

            route = RouteResult(
                id=str(route_index + 1),
                title=(
                    "مسیر پیشنهادی"
                    if route_index == 0
                    else f"مسیر جایگزین {route_index}"
                ),
                distance_meters=distance_meters,
                duration_seconds=duration_seconds,
                geometry=geometry,
                steps=steps,
                metadata={
                    "provider": "neshan",
                    "route_index": route_index,
                },
            )

            routes.append(route)

            route_features.append(
                GeoJSONFeature(
                    id=route.id,
                    geometry=geometry,
                    properties={
                        "kind": "route",
                        "title": route.title,
                        "distance_meters": distance_meters,
                        "duration_seconds": duration_seconds,
                        "is_primary": route_index == 0,
                    },
                )
            )

        endpoint_features = [
            GeoJSONFeature(
                id="route-origin",
                geometry=GeoJSONGeometry(
                    type="Point",
                    coordinates=origin.geojson_value,
                ),
                properties={
                    "kind": "route_endpoint",
                    "role": "origin",
                    "title": "مبدأ",
                },
            ),
            GeoJSONFeature(
                id="route-destination",
                geometry=GeoJSONGeometry(
                    type="Point",
                    coordinates=destination.geojson_value,
                ),
                properties={
                    "kind": "route_endpoint",
                    "role": "destination",
                    "title": "مقصد",
                },
            ),
        ]

        viewport_coordinates = [origin, destination]

        if routes:
            geometry_coordinates = routes[0].geometry.coordinates

            if isinstance(geometry_coordinates, list):
                for coordinate in geometry_coordinates:
                    if (
                        isinstance(coordinate, list)
                        and len(coordinate) >= 2
                    ):
                        viewport_coordinates.append(
                            Coordinate(
                                longitude=float(coordinate[0]),
                                latitude=float(coordinate[1]),
                            )
                        )

        primary_route = routes[0] if routes else None

        if primary_route:
            message = (
                "مسیر پیدا شد؛ فاصله تقریبی "
                f"{NeshanNormalizer._format_distance(primary_route.distance_meters)} "
                "و زمان تقریبی "
                f"{NeshanNormalizer._format_duration(primary_route.duration_seconds)} است."
            )
        else:
            message = "مسیر معتبری میان مبدأ و مقصد پیدا نشد."

        return QueryResponse(
            success=bool(routes),
            query="مسیریابی",
            operation=operation,
            message=message,
            map=build_viewport(viewport_coordinates, default_zoom=12),
            geojson=GeoJSONFeatureCollection(
                features=[
                    *route_features,
                    *endpoint_features,
                ]
            ),
            routes=routes,
            metrics=QueryMetrics(
                distance_meters=(
                    primary_route.distance_meters
                    if primary_route
                    else None
                ),
                duration_seconds=(
                    primary_route.duration_seconds
                    if primary_route
                    else None
                ),
                extra={
                    "route_count": len(routes),
                },
            ),
            tools_used=["neshan_route"],
            warnings=warnings,
        )

    @staticmethod
    def _place_feature(
        place: Place,
        *,
        feature_id: str,
    ) -> GeoJSONFeature:
        return GeoJSONFeature(
            id=feature_id,
            geometry=GeoJSONGeometry(
                type="Point",
                coordinates=place.location.geojson_value,
            ),
            properties={
                "kind": "place",
                "title": place.title,
                "address": place.address,
                "category": place.category,
                "region": place.region,
                "neighbourhood": place.neighbourhood,
                "distance_meters": place.distance_meters,
            },
        )

    @staticmethod
    def _coordinate_from_location(
        location: Any,
    ) -> Coordinate | None:
        if not isinstance(location, dict):
            return None

        longitude = location.get("x")
        latitude = location.get("y")

        if longitude is None:
            longitude = location.get("lng", location.get("longitude"))

        if latitude is None:
            latitude = location.get("lat", location.get("latitude"))

        if longitude is None or latitude is None:
            return None

        try:
            return Coordinate(
                longitude=float(longitude),
                latitude=float(latitude),
            )
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _numeric_value(value: Any) -> int:
        if isinstance(value, bool):
            return 0

        if isinstance(value, (int, float)):
            return max(0, round(value))

        if isinstance(value, dict):
            for key in ("value", "seconds", "meters"):
                nested = value.get(key)
                if isinstance(nested, (int, float)):
                    return max(0, round(nested))

        return 0

    @staticmethod
    def _format_distance(distance_meters: int) -> str:
        if distance_meters < 1000:
            return f"{distance_meters} متر"

        kilometers = distance_meters / 1000
        return f"{kilometers:.1f} کیلومتر"

    @staticmethod
    def _format_duration(duration_seconds: int) -> str:
        total_minutes = max(1, round(duration_seconds / 60))

        if total_minutes < 60:
            return f"{total_minutes} دقیقه"

        hours = total_minutes // 60
        minutes = total_minutes % 60

        if minutes == 0:
            return f"{hours} ساعت"

        return f"{hours} ساعت و {minutes} دقیقه"
