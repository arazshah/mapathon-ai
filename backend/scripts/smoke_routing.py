import json
import sys
import urllib.error
import urllib.request
from typing import Any


BASE_URL = "http://127.0.0.1:8000"
QUERY_URL = f"{BASE_URL}/api/v1/query"


def post_query(payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        QUERY_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=90,
        ) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )
        raise RuntimeError(
            f"HTTP {exc.code}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "اتصال به Backend برقرار نشد. "
            "مطمئن شوید Uvicorn روی پورت 8000 اجرا شده است."
        ) from exc

    return json.loads(raw)


def assert_route_response(
    data: dict[str, Any],
) -> None:
    assert data.get("success") is True, data
    assert data.get("operation") == "route", data

    routes = data.get("routes")
    assert isinstance(routes, list), data
    assert len(routes) >= 1, data

    places = data.get("places")
    assert isinstance(places, list), data
    assert len(places) == 2, data

    metrics = data.get("metrics")
    assert isinstance(metrics, dict), data

    distance = metrics.get("distance_meters")
    duration = metrics.get("duration_seconds")

    assert isinstance(distance, (int, float)), metrics
    assert distance > 0, metrics

    assert isinstance(duration, (int, float)), metrics
    assert duration > 0, metrics

    geojson = data.get("geojson")
    assert isinstance(geojson, dict), data
    assert geojson.get("type") == "FeatureCollection", geojson

    features = geojson.get("features")
    assert isinstance(features, list), geojson

    line_features = [
        feature
        for feature in features
        if (
            isinstance(feature, dict)
            and isinstance(feature.get("geometry"), dict)
            and feature["geometry"].get("type") == "LineString"
        )
    ]

    assert line_features, geojson

    coordinates = (
        line_features[0]
        .get("geometry", {})
        .get("coordinates", [])
    )

    assert isinstance(coordinates, list), line_features[0]
    assert len(coordinates) >= 2, line_features[0]

    first_coordinate = coordinates[0]

    assert isinstance(first_coordinate, list)
    assert len(first_coordinate) >= 2

    longitude = first_coordinate[0]
    latitude = first_coordinate[1]

    assert 44 <= longitude <= 64, (
        "ترتیب یا مقدار longitude نامعتبر است: "
        f"{first_coordinate}"
    )
    assert 24 <= latitude <= 40, (
        "ترتیب یا مقدار latitude نامعتبر است: "
        f"{first_coordinate}"
    )


def test_route_from_user_location() -> None:
    data = post_query(
        {
            "query": (
                "از موقعیت من تا فرودگاه مهرآباد "
                "با خودرو مسیر بده"
            ),
            "context": {
                "user_location": {
                    "latitude": 35.7575,
                    "longitude": 51.4098,
                },
                "city": "تهران",
                "language": "fa",
                "timezone": "Asia/Tehran",
            },
        }
    )

    assert_route_response(data)

    tools = data.get("tools_used", [])

    assert "route_from_user_location" in tools, tools

    print(
        "PASS: route_from_user_location",
        data["metrics"]["distance_meters"],
        "meters",
    )


def test_route_between_places() -> None:
    data = post_query(
        {
            "query": (
                "از میدان آزادی تهران تا میدان ونک تهران "
                "با خودرو مسیر بده"
            ),
            "context": {
                "city": "تهران",
                "language": "fa",
                "timezone": "Asia/Tehran",
            },
        }
    )

    assert_route_response(data)

    tools = data.get("tools_used", [])

    direct_tool_used = "route_between_places" in tools

    composed_tools_used = (
        tools.count("geocode_address") >= 2
        and "route_between_coordinates" in tools
    )

    assert direct_tool_used or composed_tools_used, tools

    print(
        "PASS: route_between_places",
        data["metrics"]["distance_meters"],
        "meters",
        "| tools:",
        tools,
    )


def test_missing_user_location() -> None:
    data = post_query(
        {
            "query": "از موقعیت من تا برج میلاد مسیر بده",
            "context": {
                "city": "تهران",
                "language": "fa",
                "timezone": "Asia/Tehran",
            },
        }
    )

    assert data.get("success") is False, data
    assert data.get("operation") == "clarification", data
    assert data.get("needs_clarification") is True, data
    assert data.get("clarification_question"), data

    tools = data.get("tools_used", [])

    assert "route_from_user_location" in tools, tools

    assert data.get("routes") == [], data

    print("PASS: missing_user_location clarification")


def main() -> int:
    tests = [
        test_route_from_user_location,
        test_route_between_places,
        test_missing_user_location,
    ]

    failed = 0

    for test in tests:
        try:
            test()
        except Exception as exc:
            failed += 1
            print(
                f"FAIL: {test.__name__}: {exc}",
                file=sys.stderr,
            )

    print()
    print(f"Total: {len(tests)}")
    print(f"Passed: {len(tests) - failed}")
    print(f"Failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
