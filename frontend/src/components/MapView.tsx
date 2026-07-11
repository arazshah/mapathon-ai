"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import { useEffect, useRef, useState } from "react";

import maplibregl, {
  GeoJSONSource,
  Map as MapLibreMap,
} from "maplibre-gl";

import type {
  ExpressionSpecification,
} from "maplibre-gl";

import type {
  Feature,
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

const RESULTS_SOURCE_ID = "mapathon-results";
const MARKER_LAYER_ID = "mapathon-marker-icons";
const LABEL_LAYER_ID = "mapathon-point-labels";

let rtlPluginConfigured = false;

function configureRtlText(): void {
  if (rtlPluginConfigured) {
    return;
  }

  maplibregl.setRTLTextPlugin(
    "https://unpkg.com/@mapbox/mapbox-gl-rtl-text@0.3.0/mapbox-gl-rtl-text.js",
    true,
  );

  rtlPluginConfigured = true;
}

export interface MapPlace {
  title?: string;
  name?: string;
  label?: string;
  address?: string;
  type?: string;
  category?: string;
  kind?: string;
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
      for (const geometry of feature.geometry.geometries) {
        if ("coordinates" in geometry) {
          collectCoordinates(
            geometry.coordinates,
            coordinates,
          );
        }
      }
    } else if ("coordinates" in feature.geometry) {
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
      top: 100,
      right: 100,
      bottom: 100,
      left: 100,
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
    properties.type ??
    properties.category;

  return typeof value === "string" && value.trim()
    ? value
    : "مکان انتخاب‌شده";
}

function getFeatureAddress(
  properties: GeoJsonProperties,
): string | null {
  if (!properties) {
    return null;
  }

  const value =
    properties.address ??
    properties.formatted_address ??
    properties.description;

  return typeof value === "string" && value.trim()
    ? value
    : null;
}

function createMarkerSvg(
  color: string,
  symbol: string,
): string {
  return `
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="72"
      height="88"
      viewBox="0 0 72 88"
    >
      <defs>
        <filter
          id="marker-shadow"
          x="-40%"
          y="-30%"
          width="180%"
          height="180%"
        >
          <feDropShadow
            dx="0"
            dy="4"
            stdDeviation="3"
            flood-color="#10213f"
            flood-opacity=".25"
          />
        </filter>
      </defs>

      <path
        d="M36 3C17.8 3 3 16.8 3 34.2C3 56.7 36 84 36 84S69 56.7 69 34.2C69 16.8 54.2 3 36 3Z"
        fill="${color}"
        stroke="#ffffff"
        stroke-width="4"
        filter="url(#marker-shadow)"
      />

      <circle
        cx="36"
        cy="34"
        r="20"
        fill="#ffffff"
        opacity=".98"
      />

      <text
        x="36"
        y="41"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="22"
        font-weight="700"
        fill="${color}"
      >${symbol}</text>
    </svg>
  `;
}

function addMarkerIcon(
  map: MapLibreMap,
  id: string,
  color: string,
  symbol: string,
): Promise<void> {
  return new Promise((resolve, reject) => {
    if (map.hasImage(id)) {
      resolve();
      return;
    }

    const image = new Image();

    image.onload = () => {
      if (!map.hasImage(id)) {
        map.addImage(id, image, {
          pixelRatio: 2,
          sdf: false,
        });
      }

      resolve();
    };

    image.onerror = () => {
      reject(
        new Error(
          `خطا در بارگذاری آیکون ${id}`,
        ),
      );
    };

    image.src =
      "data:image/svg+xml;charset=utf-8," +
      encodeURIComponent(
        createMarkerSvg(color, symbol),
      );
  });
}

function addAllMarkerIcons(
  map: MapLibreMap,
): Promise<void[]> {
  return Promise.all([
    addMarkerIcon(
      map,
      "marker-origin",
      "#059669",
      "●",
    ),

    addMarkerIcon(
      map,
      "marker-destination",
      "#dc2626",
      "◆",
    ),

    addMarkerIcon(
      map,
      "marker-hospital",
      "#dc2626",
      "+",
    ),

    addMarkerIcon(
      map,
      "marker-restaurant",
      "#ea580c",
      "★",
    ),

    addMarkerIcon(
      map,
      "marker-metro",
      "#7c3aed",
      "M",
    ),

    addMarkerIcon(
      map,
      "marker-pharmacy",
      "#0891b2",
      "+",
    ),

    addMarkerIcon(
      map,
      "marker-default",
      "#2563eb",
      "•",
    ),
  ]);
}

function getPlaceTypeExpression(): ExpressionSpecification {
  return [
    "downcase",
    [
      "to-string",
      [
        "coalesce",
        ["get", "type"],
        ["get", "category"],
        ["get", "kind"],
        "",
      ],
    ],
  ];
}

function getMarkerIconExpression(): ExpressionSpecification {
  const placeType = getPlaceTypeExpression();

  return [
    "case",

    [
      "==",
      ["get", "role"],
      "origin",
    ],
    "marker-origin",

    [
      "==",
      ["get", "role"],
      "start",
    ],
    "marker-origin",

    [
      "==",
      ["get", "role"],
      "destination",
    ],
    "marker-destination",

    [
      "==",
      ["get", "role"],
      "end",
    ],
    "marker-destination",

    [
      "match",
      placeType,

      [
        "hospital",
        "بیمارستان",
        "درمانی",
        "medical",
        "clinic",
      ],
      "marker-hospital",

      [
        "restaurant",
        "رستوران",
        "غذا",
        "food",
        "cafe",
        "کافه",
      ],
      "marker-restaurant",

      [
        "metro",
        "مترو",
        "ایستگاه مترو",
        "subway",
        "station",
      ],
      "marker-metro",

      [
        "pharmacy",
        "داروخانه",
        "drugstore",
      ],
      "marker-pharmacy",

      "marker-default",
    ],
  ];
}

function isPointFeature(
  feature: Feature<Geometry, GeoJsonProperties>,
): boolean {
  return feature.geometry?.type === "Point";
}

export default function MapView({
  geojson,
  selectedPlace,
}: MapViewProps) {
  const containerRef =
    useRef<HTMLDivElement | null>(null);

  const mapRef =
    useRef<MapLibreMap | null>(null);

  const [mapReady, setMapReady] =
    useState(false);

  useEffect(() => {
    configureRtlText();

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

        glyphs:
          "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",

        sources: {
          "osm-raster": {
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
            id: "osm-raster-layer",
            type: "raster",
            source: "osm-raster",
            paint: {
              "raster-saturation": -0.15,
              "raster-contrast": 0.04,
              "raster-brightness-max": 1,
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
      "top-left",
    );

    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
      }),
      "bottom-right",
    );

    map.on("load", () => {
      map.addSource(RESULTS_SOURCE_ID, {
        type: "geojson",
        data: EMPTY_GEOJSON,
      });

      map.addLayer({
        id: "mapathon-route-shadow",
        type: "line",
        source: RESULTS_SOURCE_ID,
        filter: [
          "in",
          ["geometry-type"],
          [
            "literal",
            [
              "LineString",
              "MultiLineString",
            ],
          ],
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
        source: RESULTS_SOURCE_ID,
        filter: [
          "in",
          ["geometry-type"],
          [
            "literal",
            [
              "LineString",
              "MultiLineString",
            ],
          ],
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
        source: RESULTS_SOURCE_ID,
        filter: [
          "in",
          ["geometry-type"],
          [
            "literal",
            [
              "Point",
              "MultiPoint",
            ],
          ],
        ],
        paint: {
          "circle-radius": 5,
          "circle-color": "#ffffff",
          "circle-opacity": 0.75,
        },
      });

      map.addLayer({
        id: "mapathon-points",
        type: "circle",
        source: RESULTS_SOURCE_ID,
        filter: [
          "in",
          ["geometry-type"],
          [
            "literal",
            [
              "Point",
              "MultiPoint",
            ],
          ],
        ],
        paint: {
          "circle-radius": 2,
          "circle-color": [
            "match",
            ["get", "role"],
            "origin",
            "#059669",
            "destination",
            "#dc2626",
            "#2563eb",
          ],
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1,
        },
      });

      map.addLayer({
        id: LABEL_LAYER_ID,
        type: "symbol",
        source: RESULTS_SOURCE_ID,
        filter: [
          "in",
          ["geometry-type"],
          [
            "literal",
            [
              "Point",
              "MultiPoint",
            ],
          ],
        ],
        minzoom: 11,
        layout: {
          "text-field": [
            "coalesce",
            ["get", "title"],
            ["get", "name"],
            ["get", "label"],
            ["get", "address"],
            "",
          ],

          "text-font": [
            "Noto Sans Regular",
          ],

          "text-size": [
            "interpolate",
            ["linear"],
            ["zoom"],
            10,
            10,
            15,
            13,
            18,
            15,
          ],

          "text-offset": [0, 2.25],
          "text-anchor": "top",
          "text-justify": "auto",
          "text-allow-overlap": false,
          "text-ignore-placement": false,
        },
        paint: {
          "text-color": "#172033",
          "text-halo-color": "#ffffff",
          "text-halo-width": 2.5,
          "text-halo-blur": 0.2,
        },
      });

      addAllMarkerIcons(map)
        .then(() => {
          if (!map.getLayer(MARKER_LAYER_ID)) {
            map.addLayer({
              id: MARKER_LAYER_ID,
              type: "symbol",
              source: RESULTS_SOURCE_ID,
              filter: [
                "in",
                ["geometry-type"],
                [
                  "literal",
                  [
                    "Point",
                    "MultiPoint",
                  ],
                ],
              ],
              layout: {
                "icon-image":
                  getMarkerIconExpression(),

                "icon-size": [
                  "interpolate",
                  ["linear"],
                  ["zoom"],
                  8,
                  0.34,
                  12,
                  0.44,
                  16,
                  0.52,
                ],

                "icon-anchor": "bottom",
                "icon-allow-overlap": true,
                "icon-ignore-placement": true,
              },
            });
          }

          const interactiveLayers = [
            MARKER_LAYER_ID,
            "mapathon-points",
          ];

          for (const layerId of interactiveLayers) {
            map.on(
              "mouseenter",
              layerId,
              () => {
                map.getCanvas().style.cursor =
                  "pointer";
              },
            );

            map.on(
              "mouseleave",
              layerId,
              () => {
                map.getCanvas().style.cursor =
                  "";
              },
            );

            map.on(
              "click",
              layerId,
              (event) => {
                const feature =
                  event.features?.[0];

                if (!feature) {
                  return;
                }

                if (
                  feature.geometry.type !==
                  "Point"
                ) {
                  return;
                }

                const coordinates =
                  feature.geometry.coordinates.slice() as Position;

                const title =
                  getFeatureTitle(
                    feature.properties,
                  );

                const address =
                  getFeatureAddress(
                    feature.properties,
                  );

                const popupContent =
                  document.createElement("div");

                popupContent.className =
                  "mapathon-popup";

                const titleElement =
                  document.createElement(
                    "strong",
                  );

                titleElement.textContent = title;
                popupContent.appendChild(
                  titleElement,
                );

                if (address) {
                  const addressElement =
                    document.createElement(
                      "span",
                    );

                  addressElement.textContent =
                    address;

                  popupContent.appendChild(
                    addressElement,
                  );
                }

                new maplibregl.Popup({
                  closeButton: true,
                  closeOnClick: true,
                  offset: 18,
                  maxWidth: "290px",
                })
                  .setLngLat([
                    coordinates[0],
                    coordinates[1],
                  ])
                  .setDOMContent(popupContent)
                  .addTo(map);
              },
            );
          }

          setMapReady(true);

          window.requestAnimationFrame(() => {
            map.resize();
          });
        })
        .catch((error: unknown) => {
          console.error(
            "Mapathon marker icons error:",
            error,
          );

          setMapReady(true);
        });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;

    if (!map || !mapReady) {
      return;
    }

    const source = map.getSource(
      RESULTS_SOURCE_ID,
    ) as GeoJSONSource | undefined;

    const data = geojson ?? EMPTY_GEOJSON;

    source?.setData(data);

    if (data.features.length > 0) {
      const timeoutId = window.setTimeout(() => {
        fitToGeoJSON(map, data);
      }, 120);

      return () => {
        window.clearTimeout(timeoutId);
      };
    }
  }, [geojson, mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    const coordinates =
      getPlaceCoordinates(selectedPlace);

    if (
      !map ||
      !mapReady ||
      !coordinates
    ) {
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
    </div>
  );
}
