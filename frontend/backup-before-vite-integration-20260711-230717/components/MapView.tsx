"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import maplibregl, {
  GeoJSONSource,
  Map as MapLibreMap,
} from "maplibre-gl";

import type {
  FeatureCollection,
  GeoJsonProperties,
  Geometry,
  Position,
} from "geojson";


const EMPTY_GEOJSON: FeatureCollection = {
  type: "FeatureCollection",
  features: [],
};

const TEHRAN_CENTER: [number, number] = [
  51.389,
  35.689,
];

export interface MapPlace {
  title?: string;
  name?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  lat?: number;
  lng?: number;
  location?: {
    latitude?: number;
    longitude?: number;
    lat?: number;
    lng?: number;
  };
  [key: string]: unknown;
}

interface MapViewProps {
  geojson?: FeatureCollection<
    Geometry,
    GeoJsonProperties
  > | null;
  selectedPlace?: MapPlace | null;
  loading?: boolean;
}

function collectCoordinates(
  value: unknown,
  output: [number, number][],
): void {
  if (!Array.isArray(value)) {
    return;
  }

  if (
    value.length >= 2 &&
    typeof value[0] === "number" &&
    typeof value[1] === "number"
  ) {
    const longitude = value[0];
    const latitude = value[1];

    if (
      longitude >= -180 &&
      longitude <= 180 &&
      latitude >= -90 &&
      latitude <= 90
    ) {
      output.push([longitude, latitude]);
    }

    return;
  }

  for (const item of value) {
    collectCoordinates(item, output);
  }
}

function getPlaceCoordinates(
  place?: MapPlace | null,
): [number, number] | null {
  if (!place) {
    return null;
  }

  const latitude =
    place.latitude ??
    place.lat ??
    place.location?.latitude ??
    place.location?.lat;

  const longitude =
    place.longitude ??
    place.lng ??
    place.location?.longitude ??
    place.location?.lng;

  if (
    typeof latitude !== "number" ||
    typeof longitude !== "number"
  ) {
    return null;
  }

  return [longitude, latitude];
}

function fitToGeoJSON(
  map: MapLibreMap,
  geojson: FeatureCollection,
): void {
  const coordinates: [number, number][] = [];

  for (const feature of geojson.features) {
    if (!feature.geometry) {
      continue;
    }

    if (
      feature.geometry.type ===
      "GeometryCollection"
    ) {
      for (
        const geometry
        of feature.geometry.geometries
      ) {
        if ("coordinates" in geometry) {
          collectCoordinates(
            geometry.coordinates,
            coordinates,
          );
        }
      }
    } else if (
      "coordinates" in feature.geometry
    ) {
      collectCoordinates(
        feature.geometry.coordinates,
        coordinates,
      );
    }
  }

  if (coordinates.length === 0) {
    return;
  }

  if (coordinates.length === 1) {
    map.easeTo({
      center: coordinates[0],
      zoom: 15,
      duration: 900,
    });
    return;
  }

  const bounds = coordinates.reduce(
    (currentBounds, coordinate) =>
      currentBounds.extend(coordinate),
    new maplibregl.LngLatBounds(
      coordinates[0],
      coordinates[0],
    ),
  );

  map.fitBounds(bounds, {
    padding: {
      top: 150,
      right: 70,
      bottom: 170,
      left: 70,
    },
    maxZoom: 16,
    duration: 1000,
  });
}

function getFeatureTitle(
  properties: GeoJsonProperties,
): string {
  if (!properties) {
    return "مکان انتخاب‌شده";
  }

  const value =
    properties.title ??
    properties.name ??
    properties.label ??
    properties.type;

  return typeof value === "string"
    ? value
    : "مکان انتخاب‌شده";
}

export default function MapView({
  geojson,
  selectedPlace,
  loading = false,
}: MapViewProps) {
  const containerRef =
    useRef<HTMLDivElement | null>(null);

  const mapRef =
    useRef<MapLibreMap | null>(null);

  const [mapReady, setMapReady] =
    useState(false);

  useEffect(() => {
    if (
      !containerRef.current ||
      mapRef.current
    ) {
      return;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      center: TEHRAN_CENTER,
      zoom: 11,
      minZoom: 4,
      maxZoom: 19,
      attributionControl: false,
      style: {
        version: 8,
        sources: {
          "osm-light": {
            type: "raster",
            tiles: [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution:
              "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm-light-layer",
            type: "raster",
            source: "osm-light",
            paint: {
              "raster-saturation": -0.35,
              "raster-contrast": -0.05,
              "raster-brightness-min": 0.12,
              "raster-brightness-max": 0.98,
            },
          },
        ],
      },
    });

    map.addControl(
      new maplibregl.NavigationControl({
        showCompass: true,
        showZoom: true,
      }),
      "bottom-left",
    );

    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
      }),
      "bottom-right",
    );

    map.on("load", () => {
      map.addSource("mapathon-results", {
        type: "geojson",
        data: EMPTY_GEOJSON,
      });

      map.addLayer({
        id: "mapathon-route-shadow",
        type: "line",
        source: "mapathon-results",
        filter: [
          "in",
          ["geometry-type"],
          ["literal", ["LineString", "MultiLineString"]],
        ],
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": "#ffffff",
          "line-width": 10,
          "line-opacity": 0.9,
        },
      });

      map.addLayer({
        id: "mapathon-route",
        type: "line",
        source: "mapathon-results",
        filter: [
          "in",
          ["geometry-type"],
          ["literal", ["LineString", "MultiLineString"]],
        ],
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": [
            "case",
            [
              "==",
              ["get", "is_alternative"],
              true,
            ],
            "#7c8ba1",
            "#2563eb",
          ],
          "line-width": [
            "interpolate",
            ["linear"],
            ["zoom"],
            8,
            3,
            15,
            6,
          ],
          "line-opacity": 0.92,
        },
      });

      map.addLayer({
        id: "mapathon-points-halo",
        type: "circle",
        source: "mapathon-results",
        filter: [
          "in",
          ["geometry-type"],
          ["literal", ["Point", "MultiPoint"]],
        ],
        paint: {
          "circle-radius": 11,
          "circle-color": "#ffffff",
          "circle-opacity": 0.96,
        },
      });

      map.addLayer({
        id: "mapathon-points",
        type: "circle",
        source: "mapathon-results",
        filter: [
          "in",
          ["geometry-type"],
          ["literal", ["Point", "MultiPoint"]],
        ],
        paint: {
          "circle-radius": 7,
          "circle-color": [
            "match",
            ["get", "role"],
            "origin",
            "#10b981",
            "destination",
            "#ef4444",
            "#2563eb",
          ],
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });

      map.addLayer({
        id: "mapathon-point-labels",
        type: "symbol",
        source: "mapathon-results",
        filter: [
          "in",
          ["geometry-type"],
          ["literal", ["Point", "MultiPoint"]],
        ],
        minzoom: 12,
        layout: {
          "text-field": [
            "coalesce",
            ["get", "title"],
            ["get", "name"],
            "",
          ],
          "text-size": 12,
          "text-offset": [0, 1.5],
          "text-anchor": "top",
          "text-allow-overlap": false,
        },
        paint: {
          "text-color": "#172033",
          "text-halo-color": "#ffffff",
          "text-halo-width": 2,
        },
      });

      map.on(
        "mouseenter",
        "mapathon-points",
        () => {
          map.getCanvas().style.cursor =
            "pointer";
        },
      );

      map.on(
        "mouseleave",
        "mapathon-points",
        () => {
          map.getCanvas().style.cursor = "";
        },
      );

      map.on(
        "click",
        "mapathon-points",
        (event) => {
          const feature = event.features?.[0];

          if (!feature) {
            return;
          }

          const geometry = feature.geometry;

          if (geometry.type !== "Point") {
            return;
          }

          const coordinates =
            geometry.coordinates.slice() as Position;

          const title = getFeatureTitle(
            feature.properties,
          );

          const address =
            feature.properties?.address;

          const popupContent =
            document.createElement("div");

          popupContent.className =
            "mapathon-popup";

          const titleElement =
            document.createElement("strong");

          titleElement.textContent = title;
          popupContent.appendChild(titleElement);

          if (
            typeof address === "string" &&
            address.trim()
          ) {
            const addressElement =
              document.createElement("span");

            addressElement.textContent =
              address;

            popupContent.appendChild(
              addressElement,
            );
          }

          new maplibregl.Popup({
            closeButton: true,
            closeOnClick: true,
            offset: 14,
            maxWidth: "280px",
          })
            .setLngLat([
              coordinates[0],
              coordinates[1],
            ])
            .setDOMContent(popupContent)
            .addTo(map);
        },
      );

      setMapReady(true);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;

    if (!map || !mapReady) {
      return;
    }

    const source = map.getSource(
      "mapathon-results",
    ) as GeoJSONSource | undefined;

    const data = geojson ?? EMPTY_GEOJSON;

    source?.setData(data);

    if (data.features.length > 0) {
      window.setTimeout(() => {
        fitToGeoJSON(map, data);
      }, 100);
    }
  }, [geojson, mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    const coordinates =
      getPlaceCoordinates(selectedPlace);

    if (!map || !mapReady || !coordinates) {
      return;
    }

    map.flyTo({
      center: coordinates,
      zoom: 16,
      duration: 900,
      essential: true,
    });
  }, [selectedPlace, mapReady]);

  return (
    <div className="map-shell">
      <div
        ref={containerRef}
        className="map-container"
        aria-label="نقشه نتایج مپاتون"
      />

      {!mapReady && (
        <div className="map-status">
          <span className="spinner" />
          در حال آماده‌سازی نقشه...
        </div>
      )}

      {loading && (
        <div className="map-loading">
          <span className="spinner" />
          در حال تحلیل پرس‌وجوی مکانی...
        </div>
      )}
    </div>
  );
}
