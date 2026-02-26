from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from .routers import interview
from .config import get_settings
from .services.session_store import init_db

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
settings = get_settings()
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

@app.get("/")
def read_root():
    return {"message": "Tell Your Story API"}
