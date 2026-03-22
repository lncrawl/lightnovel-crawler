import typer

from ..context import ctx

app = typer.Typer()


@app.command(help="Show current version.")
def version():
    typer.echo(f"{ctx.config.app.name} v{ctx.config.app.version}")
