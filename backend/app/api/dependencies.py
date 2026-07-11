from collections.abc import AsyncIterator

from app.clients.neshan.client import NeshanClient
from app.clients.neshan.places import NeshanPlacesService
from app.clients.neshan.routing import NeshanRoutingService
from app.config import settings
from app.services.place_application import PlaceApplicationService
from app.services.routing_application import RoutingApplicationService


async def get_neshan_client() -> AsyncIterator[NeshanClient]:
    client = NeshanClient(settings)

    try:
        yield client
    finally:
        await client.close()


async def get_neshan_places_service() -> AsyncIterator[NeshanPlacesService]:
    client = NeshanClient(settings)

    try:
        yield NeshanPlacesService(
            client=client,
            settings=settings,
        )
    finally:
        await client.close()


async def get_place_application_service(
) -> AsyncIterator[PlaceApplicationService]:
    client = NeshanClient(settings)

    try:
        neshan_service = NeshanPlacesService(
            client=client,
            settings=settings,
        )

        yield PlaceApplicationService(
            neshan=neshan_service,
        )
    finally:
        await client.close()


async def get_neshan_routing_service(
) -> AsyncIterator[NeshanRoutingService]:
    client = NeshanClient(settings)

    try:
        yield NeshanRoutingService(
            client=client,
            settings=settings,
        )
    finally:
        await client.close()


async def get_routing_application_service(
) -> AsyncIterator[RoutingApplicationService]:
    client = NeshanClient(settings)

    try:
        neshan_service = NeshanRoutingService(
            client=client,
            settings=settings,
        )

        yield RoutingApplicationService(
            neshan=neshan_service,
        )
    finally:
        await client.close()
