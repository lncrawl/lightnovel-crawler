from fastapi import APIRouter

from ...context import ctx

# The root router
router = APIRouter()


@router.post("/update-sources", summary="Update sources from the repository")
async def update() -> int:
    ctx.sources.update()
    ctx.sources.ensure_load()
    return ctx.sources.version


@router.get("/runner/status", summary="Get runner status")
def status() -> bool:
    return bool(ctx.scheduler.running)


@router.post("/runner/start", summary="Start the runner")
def start() -> bool:
    ctx.scheduler.start()
    return True


@router.post("/runner/stop", summary="Stops the runner")
def stop() -> bool:
    ctx.scheduler.stop()
    return True
