export type Location = {
  latitude: number;
  longitude: number;
};

export type MapBounds = {
  west: number;
  south: number;
  east: number;
  north: number;
};

export type MapConfiguration = {
  center?: Location | null;
  zoom?: number | null;
  bounds?: MapBounds | null;
};

export type GeoJSONGeometry = {
  type: string;
  coordinates: unknown;
};

export type GeoJSONFeature = {
  type: "Feature";
  id?: string | number;
  geometry: GeoJSONGeometry | null;
  properties?: Record<string, unknown> | null;
};

export type GeoJSONFeatureCollection = {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
};

export type Place = {
  id: string;
  title: string;
  address?: string | null;
  location: Location;
  category?: string | null;
  region?: string | null;
  neighbourhood?: string | null;
  distance_meters?: number | null;
  metadata?: Record<string, unknown>;
};

export type RouteStep = {
  instruction: string;
  name?: string | null;
  distance_meters: number;
  duration_seconds: number;
};

export type Route = {
  id: string;
  title: string;
  distance_meters: number;
  duration_seconds: number;
  geometry: GeoJSONGeometry;
  steps?: RouteStep[];
  metadata?: Record<string, unknown>;
};

export type QueryMetrics = {
  distance_meters?: number | null;
  duration_seconds?: number | null;
  total_places?: number | null;
  extra?: Record<string, unknown>;
};

export type QueryResponse = {
  success: boolean;
  query: string;
  operation: string;
  message: string;
  map?: MapConfiguration | null;
  geojson?: GeoJSONFeatureCollection | null;
  places?: Place[];
  routes?: Route[];
  metrics?: QueryMetrics | null;
  tools_used?: string[];
  warnings?: string[];
  needs_clarification?: boolean;
  clarification_question?: string | null;
  debug?: unknown;
};

export type QueryRequest = {
  query: string;
  context: {
    city: string;
    language: string;
    timezone: string;
    user_location?: Location;
  };
};
