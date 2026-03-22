from typing import Optional

import sqlmodel as sa

from ..utils.time_utils import current_timestamp


class ReadHistory(sa.SQLModel, table=True):
    __tablename__ = "read_history"  # type: ignore
    __table_args__ = (
        sa.UniqueConstraint("user_id", "chapter_id"),
        sa.Index("ix_read_history_user_created", "user_id", "created_at"),
    )

    id: Optional[int] = sa.Field(
        default=None,
        primary_key=True,
    )
    created_at: int = sa.Field(default_factory=current_timestamp, sa_type=sa.BigInteger)
    user_id: str = sa.Field(foreign_key="users.id", ondelete="CASCADE")
    chapter_id: str = sa.Field(foreign_key="chapters.id", ondelete="CASCADE")
    novel_id: str = sa.Field(foreign_key="novels.id", ondelete="CASCADE")
    volume_id: Optional[str] = sa.Field(
        default=None,
        foreign_key="volumes.id",
        ondelete="SET NULL",
    )
