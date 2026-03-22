from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse

from ..assets.version import get_version
from ..context import ctx
from ..exceptions import attach_exception_handlers
from .api import router as api
from .middleware.staticfiles import CustomStaticFiles, StaticFilesGuard

web_dir = (Path(__file__).parent / "web").absolute()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ctx.setup()
    ctx.scheduler.start()
    yield
    ctx.destroy()


app = FastAPI(
    version=get_version(),
    title="Lightnovel Crawler",
    description="Download novels from online sources and generate e-books",
    lifespan=lifespan,
)

# Add exception handlers
attach_exception_handlers(app)

# Add middleares
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)

app.add_middleware(StaticFilesGuard, prefix="/static")

# Add APIs
app.include_router(api, prefix="/api")

# Mount static files
app.mount("/static", CustomStaticFiles(), name="static")


# Mount frontend
@app.get("/{fallback:path}", include_in_schema=False)
async def serve_web(fallback: str):
    target_file = web_dir.joinpath(fallback)
    if not target_file.is_file():
        target_file = web_dir / "index.html"
    if target_file.name in {"index.html", "sw.js", "registerSW.js"}:
        return FileResponse(
            target_file,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )
    return FileResponse(target_file)
