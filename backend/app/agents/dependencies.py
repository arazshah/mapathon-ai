from dataclasses import dataclass, field
from typing import Any

from app.schemas.query import QueryContext
from app.services.place_application import PlaceApplicationService
from app.services.routing_application import RoutingApplicationService


@dataclass
class AgentDependencies:
    places: PlaceApplicationService
    routing: RoutingApplicationService
    context: QueryContext
    original_query: str

    tools_used: list[str] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(
        default_factory=list
    )
    last_tool_result: dict[str, Any] | None = None

    def record_tool(
        self,
        tool_name: str,
        result: dict[str, Any],
    ) -> None:
        self.tools_used.append(tool_name)

        self.tool_results.append(
            {
                "tool": tool_name,
                "result": result,
            }
        )

        self.last_tool_result = result

    def route_coordinates(
        self,
    ) -> list[list[float]]:
        """
        Return coordinates of the most recent usable route.

        Coordinates are returned in GeoJSON order:
        [longitude, latitude].
        """
        for item in reversed(self.tool_results):
            result = item.get("result")

            if not isinstance(result, dict):
                continue

            routes = result.get("routes")

            if isinstance(routes, list):
                for route in routes:
                    if not isinstance(route, dict):
                        continue

                    geometry = route.get("geometry")

                    if not isinstance(geometry, dict):
                        continue

                    coordinates = geometry.get("coordinates")

                    if (
                        geometry.get("type") == "LineString"
                        and isinstance(coordinates, list)
                        and len(coordinates) >= 2
                    ):
                        valid: list[list[float]] = []

                        for coordinate in coordinates:
                            if (
                                isinstance(coordinate, list)
                                and len(coordinate) >= 2
                                and isinstance(
                                    coordinate[0],
                                    (int, float),
                                )
                                and isinstance(
                                    coordinate[1],
                                    (int, float),
                                )
                            ):
                                valid.append(
                                    [
                                        float(coordinate[0]),
                                        float(coordinate[1]),
                                    ]
                                )

                        if len(valid) >= 2:
                            return valid

            geojson = result.get("geojson")

            if not isinstance(geojson, dict):
                continue

            for feature in geojson.get("features") or []:
                if not isinstance(feature, dict):
                    continue

                geometry = feature.get("geometry") or {}

                if geometry.get("type") != "LineString":
                    continue

                coordinates = geometry.get("coordinates")

                if (
                    isinstance(coordinates, list)
                    and len(coordinates) >= 2
                ):
                    valid = []

                    for coordinate in coordinates:
                        if (
                            isinstance(coordinate, list)
                            and len(coordinate) >= 2
                            and isinstance(
                                coordinate[0],
                                (int, float),
                            )
                            and isinstance(
                                coordinate[1],
                                (int, float),
                            )
                        ):
                            valid.append(
                                [
                                    float(coordinate[0]),
                                    float(coordinate[1]),
                                ]
                            )

                    if len(valid) >= 2:
                        return valid

        return []
