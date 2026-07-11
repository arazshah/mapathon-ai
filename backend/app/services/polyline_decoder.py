from __future__ import annotations


class PolylineDecodeError(ValueError):
    """Raised when an encoded polyline cannot be decoded."""


def decode_polyline(
    encoded: str,
    *,
    precision: int = 5,
) -> list[list[float]]:
    """
    Decode a Google-compatible encoded polyline.

    Neshan returns encoded points in latitude/longitude order internally.
    GeoJSON requires longitude/latitude order, so every returned coordinate
    has the following structure:

        [longitude, latitude]
    """
    if not isinstance(encoded, str) or not encoded:
        return []

    factor = 10 ** precision
    latitude = 0
    longitude = 0
    index = 0
    coordinates: list[list[float]] = []

    while index < len(encoded):
        latitude_delta, index = _decode_value(encoded, index)
        longitude_delta, index = _decode_value(encoded, index)

        latitude += latitude_delta
        longitude += longitude_delta

        coordinates.append(
            [
                round(longitude / factor, precision),
                round(latitude / factor, precision),
            ]
        )

    return coordinates


def _decode_value(
    encoded: str,
    start_index: int,
) -> tuple[int, int]:
    result = 0
    shift = 0
    index = start_index

    while True:
        if index >= len(encoded):
            raise PolylineDecodeError(
                "Encoded polyline ended unexpectedly."
            )

        value = ord(encoded[index]) - 63
        index += 1

        if value < 0:
            raise PolylineDecodeError(
                "Encoded polyline contains an invalid character."
            )

        result |= (value & 0x1F) << shift
        shift += 5

        if value < 0x20:
            break

        if shift > 60:
            raise PolylineDecodeError(
                "Encoded polyline value is too large."
            )

    decoded = ~(result >> 1) if result & 1 else result >> 1

    return decoded, index
