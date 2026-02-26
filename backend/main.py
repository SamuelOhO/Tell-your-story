from contextlib import asynccontextmanager
import logging
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .routers import interview
from .config import get_settings
from .services.session_store import check_db_health, init_db


settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("tell-your-story.api")

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
base_dir = Path(__file__).resolve().parent
static_dir = base_dir / "static"
static_dir.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(interview.router, prefix="/interview", tags=["interview"])


def _classify_http_error(exc: HTTPException) -> str:
    if exc.status_code in {401, 403}:
        return "auth"
    if exc.status_code == 422:
        return "validation"
    if exc.status_code >= 500:
        return "provider"
    return "api"


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = uuid4().hex[:8]
    start = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((perf_counter() - start) * 1000)
        logger.exception(
            "api_request_failed request_id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise
    duration_ms = int((perf_counter() - start) * 1000)
    logger.info(
        "api_request request_id=%s method=%s path=%s status_code=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "api_error error_type=validation method=%s path=%s detail=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(HTTPException)
async def typed_http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "api_error error_type=%s method=%s path=%s status_code=%s detail=%s",
        _classify_http_error(exc),
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_type = "db" if "sqlite" in type(exc).__name__.lower() else "provider"
    logger.exception(
        "api_error error_type=%s method=%s path=%s exception=%s",
        error_type,
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )


@app.get("/")
def read_root():
    return {"message": "Tell Your Story API"}


@app.get("/health")
def health_check():
    db_ok, db_detail = check_db_health()
    if db_ok:
        return {"status": "ok", "app": "up", "db": "up"}
    logger.error("api_error error_type=db path=/health detail=%s", db_detail)
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "app": "up", "db": "down", "detail": db_detail},
    )
