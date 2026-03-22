from typing import Any, Dict

import sqlmodel as sa
from sqlalchemy import event

from ..utils.text_tools import generate_uuid
from ..utils.time_utils import current_timestamp


class BaseTable(sa.SQLModel):
    id: str = sa.Field(
        default_factory=generate_uuid,
        primary_key=True,
        description="ID",
    )
    created_at: int = sa.Field(index=True, default_factory=current_timestamp, sa_type=sa.BigInteger)
    updated_at: int = sa.Field(index=True, default_factory=current_timestamp, sa_type=sa.BigInteger)
    extra: Dict[str, Any] = sa.Field(
        default_factory=dict,
        sa_type=sa.JSON,
        description="Additional metadata",
    )


@event.listens_for(BaseTable, "before_update", propagate=True)
def auto_update_timestamp(mapper, connection, target: BaseTable):
    target.updated_at = current_timestamp()
