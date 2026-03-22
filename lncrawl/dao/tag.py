from typing import Optional

import sqlmodel as sa


class Tag(sa.SQLModel, table=True):
    __tablename__ = "tags"  # type: ignore

    name: str = sa.Field(nullable=False, primary_key=True, description="Unique tag name")
    description: Optional[str] = sa.Field(default=None, description="Tag description")
