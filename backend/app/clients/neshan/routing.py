from typing import Any

from app.clients.neshan.client import NeshanClient
from app.config import Settings
from app.schemas.geo import Coordinate


class NeshanRoutingService:
    def __init__(
        self,
        client: NeshanClient,
        settings: Settings,
    ) -> None:
        self.client = client
        self.settings = settings

    async def route(
        self,
        *,
        origin: Coordinate,
        destination: Coordinate,
        vehicle_type: str = "car",
        alternatives: bool = False,
        avoid_traffic_zone: bool = False,
        avoid_odd_even_zone: bool = False,
    ) -> dict[str, Any]:
        return await self.client.request(
            "GET",
            self.settings.neshan_routing_path,
            params={
                "type": vehicle_type,
                "origin": origin.neshan_value,
                "destination": destination.neshan_value,
                "alternative": self._boolean(alternatives),
                "avoidTrafficZone": self._boolean(
                    avoid_traffic_zone
                ),
                "avoidOddEvenZone": self._boolean(
                    avoid_odd_even_zone
                ),
            },
        )

    @staticmethod
    def _boolean(value: bool) -> str:
        return "true" if value else "false"
