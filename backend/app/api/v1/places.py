from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_place_application_service
from app.schemas.geo import Coordinate
from app.services.place_application import PlaceApplicationService

router = APIRouter(
    prefix="/places",
    tags=["Normalized places"],
)


@router.get("/geocode")
async def normalized_geocode(
    address: Annotated[
        str,
        Query(min_length=2, max_length=500),
    ],
    service: Annotated[
        PlaceApplicationService,
        Depends(get_place_application_service),
    ],
) -> dict:
    return await service.geocode(address)


@router.get("/reverse")
async def normalized_reverse(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    service: Annotated[
        PlaceApplicationService,
        Depends(get_place_application_service),
    ],
) -> dict:
    return await service.reverse_geocode(
        Coordinate(
            latitude=lat,
            longitude=lng,
        )
    )


@router.get("/search")
async def normalized_search(
    term: Annotated[
        str,
        Query(min_length=2, max_length=300),
    ],
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    service: Annotated[
        PlaceApplicationService,
        Depends(get_place_application_service),
    ],
    limit: Annotated[int, Query(ge=1, le=30)] = 10,
) -> dict:
    return await service.search(
        term=term,
        location=Coordinate(
            latitude=lat,
            longitude=lng,
        ),
        limit=limit,
    )
