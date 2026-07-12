from __future__ import annotations

from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.agents.dependencies import AgentDependencies
from app.agents.prompts import SYSTEM_PROMPT
from app.config import settings
from app.schemas.geo import Coordinate
from app.schemas.query import QueryResponse


provider = OpenAIProvider(
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key,
)

model = OpenAIModel(
    settings.llm_default_model,
    provider=provider,
)

map_agent = Agent(
    model=model,
    deps_type=AgentDependencies,
    output_type=QueryResponse,
    system_prompt=SYSTEM_PROMPT,
)


@map_agent.tool
async def geocode_address(
    ctx: RunContext[AgentDependencies],
    address: str,
) -> dict:
    """
    Convert an Iranian address or place name to geographic coordinates.

    Args:
        address: Complete Persian address including city whenever known.
    """
    result = await ctx.deps.places.geocode(address)

    ctx.deps.record_tool(
        tool_name="geocode_address",
        result=result,
    )

    return result


@map_agent.tool
async def reverse_geocode(
    ctx: RunContext[AgentDependencies],
    latitude: float,
    longitude: float,
) -> dict:
    """
    Convert geographic coordinates in Iran to a formatted address.

    Args:
        latitude: Latitude between -90 and 90.
        longitude: Longitude between -180 and 180.
    """
    location = Coordinate(
        latitude=latitude,
        longitude=longitude,
    )

    result = await ctx.deps.places.reverse_geocode(location)

    ctx.deps.record_tool(
        tool_name="reverse_geocode",
        result=result,
    )

    return result


@map_agent.tool
async def search_places(
    ctx: RunContext[AgentDependencies],
    term: str,
    latitude: float,
    longitude: float,
    limit: int = 10,
) -> dict:
    """
    Search for places, businesses or services around a coordinate in Iran.

    Args:
        term: Search phrase such as داروخانه، رستوران، بیمارستان، مترو.
        latitude: Center latitude.
        longitude: Center longitude.
        limit: Number of results from 1 to 10.
    """
    safe_limit = max(1, min(limit, 10))

    location = Coordinate(
        latitude=latitude,
        longitude=longitude,
    )

    result = await ctx.deps.places.search(
        term=term,
        location=location,
        limit=safe_limit,
    )

    ctx.deps.record_tool(
        tool_name="search_places",
        result=result,
    )

    return result


@map_agent.tool
async def route_between_coordinates(
    ctx: RunContext[AgentDependencies],
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
    origin_title: str = "مبدأ",
    destination_title: str = "مقصد",
    vehicle_type: Literal["car", "motorcycle"] = "car",
    alternatives: bool = True,
    avoid_traffic_zone: bool = False,
    avoid_odd_even_zone: bool = False,
) -> dict:
    """
    Calculate a driving route between two known coordinates in Iran.

    Args:
        origin_latitude: Origin latitude.
        origin_longitude: Origin longitude.
        destination_latitude: Destination latitude.
        destination_longitude: Destination longitude.
        origin_title: Human-readable origin title.
        destination_title: Human-readable destination title.
        vehicle_type: Either car or motorcycle.
        alternatives: Return alternative routes when available.
        avoid_traffic_zone: Avoid traffic restriction zones.
        avoid_odd_even_zone: Avoid odd-even restriction zones.
    """
    origin = Coordinate(
        latitude=origin_latitude,
        longitude=origin_longitude,
    )
    destination = Coordinate(
        latitude=destination_latitude,
        longitude=destination_longitude,
    )

    result = await ctx.deps.routing.route(
        origin=origin,
        destination=destination,
        origin_title=origin_title,
        destination_title=destination_title,
        vehicle_type=vehicle_type,
        alternatives=alternatives,
        avoid_traffic_zone=avoid_traffic_zone,
        avoid_odd_even_zone=avoid_odd_even_zone,
    )

    ctx.deps.record_tool(
        tool_name="route_between_coordinates",
        result=result,
    )

    return result


@map_agent.tool
async def route_between_places(
    ctx: RunContext[AgentDependencies],
    origin_address: str,
    destination_address: str,
    vehicle_type: Literal["car", "motorcycle"] = "car",
    alternatives: bool = True,
    avoid_traffic_zone: bool = False,
    avoid_odd_even_zone: bool = False,
) -> dict:
    """
    Geocode two Iranian place names or addresses and calculate a route.

    Use this tool whenever the origin or destination is written as a
    place name, street, address, landmark, neighborhood, or city in
    the user's query.

    This tool must also be used when the user describes their current
    location in text, for example:
    «من در خیابان دانشکده کنار ترک مال ارومیه هستم».

    Preserve the city in ambiguous addresses.

    Args:
        origin_address: Origin place name or complete address.
        destination_address: Destination place name or complete address.
        vehicle_type: Either car or motorcycle.
        alternatives: Return alternative routes when available.
        avoid_traffic_zone: Avoid traffic restriction zones.
        avoid_odd_even_zone: Avoid odd-even restriction zones.
    """
    origin_result = await ctx.deps.places.geocode(origin_address)
    destination_result = await ctx.deps.places.geocode(
        destination_address
    )

    origin = _extract_first_location(origin_result)
    destination = _extract_first_location(destination_result)

    if origin is None or destination is None:
        result = _clarification_result(
            message=(
                "برای محاسبه مسیر، موقعیت دقیق مبدأ و مقصد "
                "قابل تشخیص نبود."
            ),
            question=(
                "لطفاً نام یا آدرس دقیق‌تر مبدأ و مقصد را "
                "همراه با نام شهر وارد کنید."
            ),
        )

        ctx.deps.record_tool(
            tool_name="route_between_places",
            result=result,
        )

        return result

    result = await ctx.deps.routing.route(
        origin=origin,
        destination=destination,
        origin_title=origin_address,
        destination_title=destination_address,
        vehicle_type=vehicle_type,
        alternatives=alternatives,
        avoid_traffic_zone=avoid_traffic_zone,
        avoid_odd_even_zone=avoid_odd_even_zone,
    )

    ctx.deps.record_tool(
        tool_name="route_between_places",
        result=result,
    )

    return result


@map_agent.tool
async def route_from_user_location(
    ctx: RunContext[AgentDependencies],
    destination_address: str,
    vehicle_type: Literal["car", "motorcycle"] = "car",
    alternatives: bool = True,
    avoid_traffic_zone: bool = False,
    avoid_odd_even_zone: bool = False,
) -> dict:
    """
    Calculate a route from context.user_location to an Iranian destination.

    Use this tool only when:
    - the user has not provided a textual origin; and
    - context.user_location is available.

    Do not use this tool when the user has written their current
    address, street, landmark, neighborhood, or city in the query.
    In that case use route_between_places.

    Examples for this tool:
    «از موقعیت فعلی من به میدان ونک برو»
    «از اینجا به فرودگاه امام خمینی مسیر بده»
    when no textual origin is included in the query.

    Args:
        destination_address: Destination place name or complete address.
        vehicle_type: Either car or motorcycle.
        alternatives: Return alternative routes when available.
        avoid_traffic_zone: Avoid traffic restriction zones.
        avoid_odd_even_zone: Avoid odd-even restriction zones.
    """
    origin = ctx.deps.context.user_location

    if origin is None:
        result = _clarification_result(
            message="موقعیت فعلی کاربر در Context موجود نیست.",
            question=(
                "لطفاً موقعیت فعلی خود را روی نقشه مشخص کنید "
                "یا مبدأ مسیر را بنویسید."
            ),
        )

        ctx.deps.record_tool(
            tool_name="route_from_user_location",
            result=result,
        )

        return result

    destination_result = await ctx.deps.places.geocode(
        destination_address
    )
    destination = _extract_first_location(destination_result)

    if destination is None:
        result = _clarification_result(
            message=(
                f"موقعیت مقصد «{destination_address}» "
                "قابل تشخیص نبود."
            ),
            question=(
                "لطفاً نام یا آدرس دقیق‌تر مقصد را همراه "
                "با نام شهر وارد کنید."
            ),
        )

        ctx.deps.record_tool(
            tool_name="route_from_user_location",
            result=result,
        )

        return result

    result = await ctx.deps.routing.route(
        origin=origin,
        destination=destination,
        origin_title="موقعیت فعلی من",
        destination_title=destination_address,
        vehicle_type=vehicle_type,
        alternatives=alternatives,
        avoid_traffic_zone=avoid_traffic_zone,
        avoid_odd_even_zone=avoid_odd_even_zone,
    )

    ctx.deps.record_tool(
        tool_name="route_from_user_location",
        result=result,
    )

    return result



@map_agent.tool
async def search_places_along_route(
    ctx: RunContext[AgentDependencies],
    term: str,
    radius_meters: int = 500,
    limit: int = 10,
) -> dict:
    """
    Search any generic place type near the current route.

    Use this tool only after a route tool has successfully run.

    Examples of term:
    داروخانه، رستوران، بیمارستان، پمپ بنزین،
    بانک، سوپرمارکت، کافه، پارک، مترو.

    Args:
        term: Generic Persian search phrase.
        radius_meters: Maximum distance from route, from 100 to 3000.
        limit: Maximum number of results, from 1 to 30.
    """
    route_coordinates = ctx.deps.route_coordinates()

    if len(route_coordinates) < 2:
        result = _clarification_result(
            message=(
                "برای جستجو در مسیر، ابتدا باید یک مسیر معتبر "
                "محاسبه شود."
            ),
            question=(
                "لطفاً مبدأ و مقصد را مشخص کنید تا ابتدا مسیر "
                "محاسبه شود."
            ),
        )

        ctx.deps.record_tool(
            tool_name="search_places_along_route",
            result=result,
        )

        return result

    result = await ctx.deps.places.search_along_route(
        term=term,
        route_coordinates=route_coordinates,
        radius_meters=max(100, min(radius_meters, 3000)),
        limit=max(1, min(limit, 30)),
    )

    ctx.deps.record_tool(
        tool_name="search_places_along_route",
        result=result,
    )

    return result

def _extract_first_location(
    payload: dict,
) -> Coordinate | None:
    places = payload.get("places")

    if not isinstance(places, list) or not places:
        return None

    first_place = places[0]

    if not isinstance(first_place, dict):
        return None

    location = first_place.get("location")

    if not isinstance(location, dict):
        return None

    try:
        return Coordinate.model_validate(location)
    except Exception:
        return None


def _clarification_result(
    *,
    message: str,
    question: str,
) -> dict:
    return {
        "success": False,
        "operation": "clarification",
        "message": message,
        "map": None,
        "geojson": {
            "type": "FeatureCollection",
            "features": [],
        },
        "places": [],
        "routes": [],
        "metrics": {
            "total_places": 0,
        },
        "warnings": [],
        "needs_clarification": True,
        "clarification_question": question,
    }
