from alembic import context

from lncrawl.context import ctx
from lncrawl.dao import SQLModel

if context.is_offline_mode():
    raise Exception("Offline mode is not supported")

with ctx.db.engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=SQLModel.metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()
