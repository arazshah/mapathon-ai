from typing import Any

from app.clients.neshan.client import NeshanClient
from app.config import Settings
from app.schemas.geo import Coordinate


class NeshanPlacesService:
    def __init__(
        self,
        client: NeshanClient,
        settings: Settings,
    ) -> None:
        self.client = client
        self.settings = settings

    async def search(
        self,
        term: str,
        location: Coordinate,
    ) -> dict[str, Any]:
        return await self.client.request(
            "GET",
            self.settings.neshan_search_path,
            params={
                "term": term,
                "lat": location.latitude,
                "lng": location.longitude,
            },
        )

    async def geocode(
        self,
        address: str,
    ) -> dict[str, Any]:
        return await self.client.request(
            "GET",
            self.settings.neshan_geocoding_path,
            params={"address": address},
        )

    async def reverse_geocode(
        self,
        location: Coordinate,
    ) -> dict[str, Any]:
        return await self.client.request(
            "GET",
            self.settings.neshan_reverse_geocoding_path,
            params={
                "lat": location.latitude,
                "lng": location.longitude,
            },
        )
