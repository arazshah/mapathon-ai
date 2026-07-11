from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.geo import (
    Coordinate,
    GeoJSONFeatureCollection,
    MapViewport,
    Place,
    RouteResult,
)


class OperationType(StrEnum):
    search = "search"
    geocode = "geocode"
    reverse_geocode = "reverse_geocode"
    route = "route"
    route_no_traffic = "route_no_traffic"
    predictive_route = "predictive_route"
    typical_route = "typical_route"
    pedestrian_route = "pedestrian_route"
    tsp = "tsp"
    distance_matrix = "distance_matrix"
    isochrone = "isochrone"
    isodistance = "isodistance"
    map_matching = "map_matching"
    compound = "compound"
    clarification = "clarification"


class QueryContext(BaseModel):
    user_location: Coordinate | None = None
    city: str | None = None
    language: str = "fa"
    timezone: str = "Asia/Tehran"


class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    context: QueryContext = Field(default_factory=QueryContext)


class QueryMetrics(BaseModel):
    distance_meters: int | None = None
    duration_seconds: int | None = None
    total_places: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    success: bool = True
    query: str
    operation: OperationType
    message: str

    map: MapViewport | None = None
    geojson: GeoJSONFeatureCollection = Field(
        default_factory=GeoJSONFeatureCollection
    )

    places: list[Place] = Field(default_factory=list)
    routes: list[RouteResult] = Field(default_factory=list)
    metrics: QueryMetrics = Field(default_factory=QueryMetrics)

    tools_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    needs_clarification: bool = False
    clarification_question: str | None = None

    debug: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    request_id: str | None = None
