import sqlmodel as sa

from ._base import BaseTable


class Volume(BaseTable, table=True):
    __tablename__ = "volumes"  # type: ignore
    __table_args__ = (
        sa.UniqueConstraint("novel_id", "serial"),
        sa.Index("ix_volume_novel_id", "novel_id"),
        sa.Index("ix_volume_novel_serial", "novel_id", "serial"),
    )

    novel_id: str = sa.Field(
        foreign_key="novels.id",
        ondelete="CASCADE",
    )
    serial: int = sa.Field(
        description="Serial number of the volume",
    )
    title: str = sa.Field(
        description="Name of the volume",
    )
    chapter_count: int = sa.Field(
        default=0,
        description="Number of available chapters",
    )
