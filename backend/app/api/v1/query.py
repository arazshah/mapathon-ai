import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.agents.dependencies import AgentDependencies
from app.agents.map_agent import (
    map_agent,
    search_places_along_route_for_dependencies,
)
from app.api.dependencies import (
    get_place_application_service,
    get_routing_application_service,
)
from app.config import settings
from app.schemas.query import QueryRequest, QueryResponse
from app.services.place_application import PlaceApplicationService
from app.services.routing_application import RoutingApplicationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Mapathon Agent"])

def _is_compound_route_search_query(query: str) -> bool:
    """تشخیص درخواست هم‌زمان مسیریابی و جستجوی مکان."""

    normalized = " ".join((query or "").split())

    route_terms = (
        "مسیریابی",
        "مسیر",
        "بروم",
        "برو",
        "برسان",
        "حرکت کنم",
        "راه",
    )

    place_terms = (
        "داروخانه",
        "رستوران",
        "بیمارستان",
        "پمپ بنزین",
        "بانک",
        "فروشگاه",
        "سوپرمارکت",
        "کافه",
        "پارک",
        "مترو",
    )

    return (
        any(term in normalized for term in route_terms)
        and any(term in normalized for term in place_terms)
    )


def _extract_compound_search_term(query: str) -> str | None:
    """استخراج نوع مکان از درخواست ترکیبی."""

    normalized = " ".join((query or "").split())

    place_terms = (
        "داروخانه",
        "رستوران",
        "بیمارستان",
        "پمپ بنزین",
        "بانک",
        "فروشگاه",
        "سوپرمارکت",
        "کافه",
        "پارک",
        "مترو",
    )

    for term in place_terms:
        if term in normalized:
            return term

    return None



@router.post(
    "/query",
    response_model=QueryResponse,
)
async def query_mapathon(
    payload: QueryRequest,
    places: Annotated[
        PlaceApplicationService,
        Depends(get_place_application_service),
    ],
    routing: Annotated[
        RoutingApplicationService,
        Depends(get_routing_application_service),
    ],
) -> QueryResponse:
    started_at = time.perf_counter()
    logger.info(
        "query_started query=%r",
        payload.query[:200],
    )
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY تنظیم نشده است.",
        )

    dependencies = AgentDependencies(
        places=places,
        routing=routing,
        context=payload.context,
        original_query=payload.query,
    )

    context_description = payload.context.model_dump_json(
        exclude_none=True
    )

    user_prompt = f"""
پرسش اصلی کاربر:
{payload.query}

Context کاربر:
{context_description}

قواعد پاسخ:
- query باید دقیقاً برابر پرسش اصلی کاربر باشد.
- مختصات، آدرس و مسیر تولید نکن.
- برای درخواست مسیر در مسیر، ابتدا route و سپس
  search_places_along_route را اجرا کن.
- اگر کاربر مبدأ را در متن نوشته است، مانند «من در ... هستم»،
  «در ... ایستاده‌ام»، «کنار ... هستم» یا «از ... حرکت می‌کنم»،
  از route_between_places استفاده کن و منتظر user_location یا GPS نمان.
- فقط وقتی از route_from_user_location استفاده کن که مبدأ متنی
  در پرسش وجود نداشته باشد و کاربر واقعاً به موقعیت موجود در
  context.user_location ارجاع داده باشد.
- عبارت «به خیابان حسنی به یک داروخانه بروم» را به‌صورت درخواست
  ترکیبی تفسیر کن: مقصد مسیر «خیابان حسنی» و عبارت جستجو
  «داروخانه» است. ابتدا route و سپس search_places_along_route
  را اجرا کن.
- اگر شهر در پرسش مشخص شده است، آن را به آدرس‌های مبهم مقصد
  و مبدأ اضافه کن.
- اگر اطلاعات لازم موجود نیست، clarification تولید کن.
"""

    try:
        result = await map_agent.run(
            user_prompt,
            deps=dependencies,
        )
    except Exception as exc:
        logger.exception(
            "mapathon_agent_failed duration=%.2fs query=%r",
            time.perf_counter() - started_at,
            payload.query[:200],
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "عامل هوشمند نتوانست درخواست را پردازش کند. "
                "اتصال AvalAI، نشان و تنظیمات مدل را بررسی کنید."
            ),
        ) from exc
    
    logger.info(
        "query_agent_finished duration=%.2fs tools=%s tool_results=%d",
        time.perf_counter() - started_at,
        dependencies.tools_used,
        len(dependencies.tool_results),
    )

    # اجرای قطعی بخش دوم درخواست‌های ترکیبی.
    # مدل ممکن است پس از route، ابزار جستجو را فراخوانی نکند.
    if _is_compound_route_search_query(payload.query):
        search_term = _extract_compound_search_term(payload.query)

        has_route = any(
            tool_name in dependencies.tools_used
            for tool_name in (
                "route_between_places",
                "route_between_coordinates",
                "route_from_user_location",
            )
        )

        already_searched = (
            "search_places_along_route"
            in dependencies.tools_used
        )

        if search_term and has_route and not already_searched:
            logger.info(
                "forcing_along_route_search term=%s",
                search_term,
            )

            await search_places_along_route_for_dependencies(
                deps=dependencies,
                term=search_term,
                radius_meters=500,
                limit=10,
            )


    if dependencies.tool_results:
        merged = merge_tool_results(
            query=payload.query,
            tool_results=dependencies.tool_results,
            tools_used=list(dict.fromkeys(dependencies.tools_used)),
        )

        return build_deterministic_response(
            query=payload.query,
            tool_result=merged,
            tools_used=list(dict.fromkeys(dependencies.tools_used)),
        )

    response = result.output
    response.query = payload.query
    response.tools_used = list(dict.fromkeys(dependencies.tools_used))

    if not settings.include_agent_debug:
        response.debug = None

    logger.info(
        "query_finished duration=%.2fs operation=%s",
        time.perf_counter() - started_at,
        response.operation,
    )
    
    return response


def merge_tool_results(
    *,
    query: str,
    tool_results: list[dict[str, Any]],
    tools_used: list[str],
) -> dict[str, Any]:
    if len(tool_results) == 1:
        result = tool_results[0].get("result")

        if isinstance(result, dict):
            normalized = dict(result)

            places = normalized.get("places")
            if isinstance(places, list):
                normalized["places"] = [
                    place
                    for place in places
                    if isinstance(place, dict)
                    and place.get("category")
                    not in {
                        "geocoded_address",
                        "route_origin",
                        "route_destination",
                    }
                ]

            metrics = normalized.get("metrics")
            if not isinstance(metrics, dict):
                metrics = {}

            metrics["total_places"] = len(normalized["places"])
            normalized["metrics"] = metrics

            return normalized

    all_places: list[dict[str, Any]] = []
    all_routes: list[dict[str, Any]] = []
    all_features: list[dict[str, Any]] = []
    warnings: list[str] = []
    messages: list[str] = []
    maps: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    seen_places: set[str] = set()
    seen_routes: set[str] = set()
    seen_features: set[str] = set()

    operation_names: list[str] = []

    for item in tool_results:
        result = item.get("result")

        if not isinstance(result, dict):
            continue

        operation = result.get("operation")

        if isinstance(operation, str):
            operation_names.append(operation)

        message = result.get("message")

        if isinstance(message, str) and message.strip():
            messages.append(message.strip())

        current_map = result.get("map")

        if isinstance(current_map, dict):
            maps.append(current_map)

        for warning in result.get("warnings") or []:
            if (
                isinstance(warning, str)
                and warning.strip()
                and warning not in warnings
            ):
                warnings.append(warning)

        for place in result.get("places") or []:
            if not isinstance(place, dict):
                continue

            place_id = place.get("id")

            if not isinstance(place_id, str):
                location = place.get("location") or {}
                place_id = (
                    f"{place.get('title', '')}|"
                    f"{location.get('latitude', '')}|"
                    f"{location.get('longitude', '')}"
                )

            if place_id in seen_places:
                continue

            seen_places.add(place_id)
            all_places.append(place)

        for route in result.get("routes") or []:
            if not isinstance(route, dict):
                continue

            route_id = str(
                route.get("id")
                or route.get("title")
                or len(all_routes)
            )

            if route_id in seen_routes:
                continue

            seen_routes.add(route_id)
            all_routes.append(route)

        geojson = result.get("geojson")

        if isinstance(geojson, dict):
            for feature in geojson.get("features") or []:
                if not isinstance(feature, dict):
                    continue

                feature_id = str(
                    feature.get("id")
                    or (
                        feature.get("properties") or {}
                    ).get("title")
                    or len(all_features)
                )

                if feature_id in seen_features:
                    continue

                seen_features.add(feature_id)
                all_features.append(feature)

        current_metrics = result.get("metrics")

        if isinstance(current_metrics, dict):
            for key, value in current_metrics.items():
                if key == "extra" and isinstance(value, dict):
                    extra = metrics.setdefault("extra", {})
                    extra.update(value)
                elif value is not None:
                    metrics[key] = value

    if all_routes or "search" in operation_names:
        all_places = [
            place
            for place in all_places
            if (
                place.get("category")
                not in {
                    "geocoded_address",
                    "route_origin",
                    "route_destination",
                }
            )
        ]

    metrics["total_places"] = len(all_places)

    if all_routes:
        operation = "compound"
    elif operation_names:
        operation = operation_names[-1]
    else:
        operation = "compound"

    if len(all_routes) > 0 and len(all_places) > 0:
        message = (
            f"مسیر و {len(all_places)} مکان مرتبط "
            "با موفقیت پیدا شد."
        )
    elif messages:
        message = " ".join(dict.fromkeys(messages))
    else:
        message = "نتیجه مکانی آماده شد."

    return {
        "success": bool(all_places or all_routes),
        "query": query,
        "operation": operation,
        "message": message,
        "map": maps[0] if maps else None,
        "geojson": {
            "type": "FeatureCollection",
            "features": all_features,
        },
        "places": all_places,
        "routes": all_routes,
        "metrics": metrics,
        "warnings": warnings,
        "needs_clarification": False,
        "clarification_question": None,
        "tools_used": tools_used,
    }


def build_deterministic_response(
    *,
    query: str,
    tool_result: dict[str, Any],
    tools_used: list[str],
) -> QueryResponse:
    data = dict(tool_result)

    places = data.get("places")
    routes = data.get("routes")

    if not isinstance(places, list):
        places = []

    if not isinstance(routes, list):
        routes = []

    operation = str(
        data.get("operation", "clarification")
    )

    needs_clarification = bool(
        data.get("needs_clarification", False)
    )

    if operation in {
        "search",
        "search_along_route",
    }:
        success = bool(places)
    elif operation in {
        "geocode",
        "reverse_geocode",
        "route",
        "route_no_traffic",
        "predictive_route",
        "typical_route",
        "pedestrian_route",
        "compound",
    }:
        success = bool(places or routes)
    elif operation == "clarification":
        success = False
        needs_clarification = True
    else:
        success = bool(data.get("success", True))

    raw_metrics = data.get("metrics")

    if not isinstance(raw_metrics, dict):
        raw_metrics = {}

    known_metric_keys = {
        "distance_meters",
        "duration_seconds",
        "total_places",
        "extra",
    }

    raw_extra = raw_metrics.get("extra")

    metrics_extra = (
        dict(raw_extra)
        if isinstance(raw_extra, dict)
        else {}
    )

    for key, value in raw_metrics.items():
        if key not in known_metric_keys:
            metrics_extra[key] = value

    normalized_metrics = {
        "distance_meters": raw_metrics.get(
            "distance_meters"
        ),
        "duration_seconds": raw_metrics.get(
            "duration_seconds"
        ),
        "total_places": raw_metrics.get(
            "total_places",
            len(places),
        ),
        "extra": metrics_extra,
    }

    geojson = data.get("geojson")

    if not isinstance(geojson, dict):
        geojson = {
            "type": "FeatureCollection",
            "features": [],
        }

    data.update(
        {
            "success": success,
            "query": query,
            "operation": operation,
            "message": data.get(
                "message",
                "نتیجه مکانی آماده شد.",
            ),
            "geojson": geojson,
            "places": places,
            "routes": routes,
            "metrics": normalized_metrics,
            "tools_used": tools_used,
            "warnings": data.get("warnings") or [],
            "needs_clarification": needs_clarification,
            "clarification_question": data.get(
                "clarification_question"
            ),
            "debug": None,
        }
    )

    return QueryResponse.model_validate(data)
