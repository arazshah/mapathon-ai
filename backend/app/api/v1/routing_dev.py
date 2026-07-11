from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_neshan_routing_service
from app.clients.neshan.routing import NeshanRoutingService
from app.schemas.geo import Coordinate

router = APIRouter(
    prefix="/neshan",
    tags=["Neshan routing development"],
)


@router.get("/route")
async def raw_route(
    origin_lat: Annotated[float, Query(ge=-90, le=90)],
    origin_lng: Annotated[float, Query(ge=-180, le=180)],
    destination_lat: Annotated[float, Query(ge=-90, le=90)],
    destination_lng: Annotated[float, Query(ge=-180, le=180)],
    service: Annotated[
        NeshanRoutingService,
        Depends(get_neshan_routing_service),
    ],
    vehicle_type: Literal[
        "car",
        "motorcycle",
    ] = "car",
    alternative: bool = False,
    avoid_traffic_zone: bool = False,
    avoid_odd_even_zone: bool = False,
) -> dict:
    origin = Coordinate(
        latitude=origin_lat,
        longitude=origin_lng,
    )

    destination = Coordinate(
        latitude=destination_lat,
        longitude=destination_lng,
    )

    return await service.route(
        origin=origin,
        destination=destination,
        vehicle_type=vehicle_type,
        alternatives=alternative,
        avoid_traffic_zone=avoid_traffic_zone,
        avoid_odd_even_zone=avoid_odd_even_zone,
    )
