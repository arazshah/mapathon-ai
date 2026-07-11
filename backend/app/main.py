from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.neshan import router as neshan_router
from app.api.v1.places import router as places_router
from app.api.v1.query import router as query_router
from app.api.v1.routing_dev import router as routing_dev_router
from app.config import settings
from app.core.exception_handlers import register_exception_handlers


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info(
        "Starting %s in %s mode",
        settings.app_name,
        settings.app_env,
    )
    yield
    logging.getLogger(__name__).info(
        "Stopping %s",
        settings.app_name,
    )


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "Natural-language geospatial platform powered by "
        "Pydantic AI and Neshan APIs"
    ),
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    neshan_router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    places_router,
    prefix=settings.api_v1_prefix,
)


app.include_router(
    query_router,
    prefix=settings.api_v1_prefix,
)


app.include_router(
    routing_dev_router,
    prefix=settings.api_v1_prefix,
)


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": "0.2.0",
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }
