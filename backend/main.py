from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from .routers import interview

app = FastAPI()
base_dir = Path(__file__).resolve().parent
static_dir = base_dir / "static"
static_dir.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(interview.router, prefix="/interview", tags=["interview"])

@app.get("/")
def read_root():
    return {"message": "Tell Your Story API"}
