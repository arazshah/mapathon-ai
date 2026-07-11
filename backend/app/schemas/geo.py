from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @property
    def neshan_value(self) -> str:
        return f"{self.latitude},{self.longitude}"

    @property
    def geojson_value(self) -> list[float]:
        return [self.longitude, self.latitude]


class MapBounds(BaseModel):
    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)


class MapViewport(BaseModel):
    center: Coordinate
    zoom: float = Field(default=13, ge=1, le=22)
    bounds: MapBounds | None = None


class GeoJSONGeometry(BaseModel):
    type: Literal[
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
    ]
    coordinates: Any


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str | int | None = None
    geometry: GeoJSONGeometry
    properties: dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeature] = Field(default_factory=list)


class Place(BaseModel):
    id: str | None = None
    title: str
    address: str | None = None
    location: Coordinate
    category: str | None = None
    region: str | None = None
    neighbourhood: str | None = None
    distance_meters: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteStep(BaseModel):
    instruction: str | None = None
    name: str | None = None
    distance_meters: int | None = None
    duration_seconds: int | None = None


class RouteResult(BaseModel):
    id: str | None = None
    title: str | None = None
    distance_meters: int = Field(ge=0)
    duration_seconds: int = Field(ge=0)
    geometry: GeoJSONGeometry
    steps: list[RouteStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("geometry")
    @classmethod
    def geometry_must_be_line(cls, value: GeoJSONGeometry) -> GeoJSONGeometry:
        if value.type not in {"LineString", "MultiLineString"}:
            raise ValueError("Route geometry must be a line geometry")
        return value
