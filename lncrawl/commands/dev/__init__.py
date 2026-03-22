import typer

from .migrate import app as migrate

app = typer.Typer(
    help="Run development commands.",
    no_args_is_help=True,
)

app.add_typer(migrate, name="migrate")


@app.callback()
def dev():
    pass
