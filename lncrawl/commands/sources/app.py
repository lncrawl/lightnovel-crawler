import typer

from ...context import ctx

app = typer.Typer(
    help="Manage sources.",
    no_args_is_help=True,
)


@app.callback()
def sources():
    ctx.setup()
    ctx.sources.ensure_load()
