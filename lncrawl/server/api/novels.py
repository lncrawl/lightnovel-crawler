from typing import List

from fastapi import APIRouter, Depends, Path, Query

from ...context import ctx
from ...dao import Artifact, Chapter, Novel, Volume
from ..models import Paginated, SourceItem
from ..security import ensure_admin

# The root router
router = APIRouter()


@router.get(
    "s",
    summary="Returns a list of novels",
)
def list_novels(
    search: str = Query(default="", help="Search query"),
    offset: int = Query(default=0, help="Offset"),
    limit: int = Query(default=20, le=100, help="Limit"),
    domain: str = Query(default="", help="Domain name"),
) -> Paginated[Novel]:
    return ctx.novels.list(
        limit=limit,
        offset=offset,
        search=search.strip(),
        domain=domain.strip(),
    )


@router.get(
    "/sources",
    summary="Returns a list of sources that are used in available novels",
)
def list_sources() -> List[SourceItem]:
    return ctx.novels.list_sources()


@router.get("/{novel_id}", summary="Returns a novel")
def get_novel(
    novel_id: str = Path(),
) -> Novel:
    return ctx.novels.get(novel_id)


@router.get("/{novel_id}/volumes", summary="Gets volumes")
async def get_novel_volumes(
    novel_id: str = Path(),
) -> List[Volume]:
    return ctx.volumes.list(novel_id=novel_id)


@router.get("/{novel_id}/chapters", summary="Gets all chapters")
async def get_novel_chapters(
    novel_id: str = Path(),
    offset: int = Query(default=0),
    limit: int = Query(default=20, le=100),
) -> Paginated[Chapter]:
    return ctx.chapters.list_page(
        limit=limit,
        offset=offset,
        novel_id=novel_id,
    )


@router.get("/{novel_id}/artifacts", summary="Gets latest artifacts")
async def get_novel_artifacts(
    novel_id: str = Path(),
) -> List[Artifact]:
    return ctx.artifacts.list_latest(novel_id=novel_id)


@router.delete("/{novel_id}", summary="Removes a novel", dependencies=[Depends(ensure_admin)])
def delete_novel(
    novel_id: str = Path(),
) -> bool:
    ctx.novels.delete(novel_id)
    return True
