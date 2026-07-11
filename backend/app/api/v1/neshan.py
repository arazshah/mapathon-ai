from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_neshan_places_service
from app.clients.neshan.places import NeshanPlacesService
from app.schemas.geo import Coordinate

router = APIRouter(prefix="/neshan", tags=["Neshan development"])


@router.get("/search")
async def search(
    term: Annotated[str, Query(min_length=2, max_length=300)],
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    service: Annotated[
        NeshanPlacesService,
        Depends(get_neshan_places_service),
    ],
) -> dict:
    return await service.search(
        term=term,
        location=Coordinate(latitude=lat, longitude=lng),
    )


@router.get("/geocode")
async def geocode(
    address: Annotated[str, Query(min_length=2, max_length=500)],
    service: Annotated[
        NeshanPlacesService,
        Depends(get_neshan_places_service),
    ],
) -> dict:
    return await service.geocode(address)


@router.get("/reverse")
async def reverse_geocode(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    service: Annotated[
        NeshanPlacesService,
        Depends(get_neshan_places_service),
    ],
) -> dict:
    return await service.reverse_geocode(
        Coordinate(latitude=lat, longitude=lng)
    )
