from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mapathon API"
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    api_v1_prefix: str = "/api/v1"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.avalai.ir/v1"
    llm_default_model: str = "gpt-4o-mini"

    neshan_api_key: str = ""
    neshan_base_url: str = "https://api.neshan.org"
    neshan_timeout_seconds: float = Field(default=30, ge=1, le=120)

    neshan_search_path: str = "/v1/search"
    neshan_geocoding_path: str = "/v4/geocoding"
    neshan_reverse_geocoding_path: str = "/v5/reverse"
    neshan_routing_path: str = "/v4/direction"
    neshan_no_traffic_routing_path: str = "/v4/direction/no-traffic"
    neshan_historical_routing_path: str = "/v4/direction/historical"
    neshan_typical_routing_path: str = "/v4/direction/typical"
    neshan_pedestrian_routing_path: str = "/v4/direction/pedestrian"
    neshan_tsp_path: str = "/v3/trip"
    neshan_distance_matrix_path: str = "/v1/distance-matrix"
    neshan_isochrone_path: str = "/v1/isochrone"
    neshan_map_matching_path: str = "/v1/map-matching"

    default_country: str = "ایران"
    default_city: str = ""
    default_latitude: float = 32.4279
    default_longitude: float = 53.6880
    default_zoom: float = 5

    cors_origins: str = (
        "http://localhost:3000,"
        "https://mapathon.ir,"
        "https://www.mapathon.ir"
    )

    log_level: str = "INFO"
    include_agent_debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
