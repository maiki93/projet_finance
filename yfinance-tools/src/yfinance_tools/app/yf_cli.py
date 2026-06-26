"""
CLI tool
"""

import logging
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from yfinance_tools.bootstrap import bootstrap_app
from yfinance_tools.domain import Asset
from yfinance_tools.domain.exceptions import YFinanceToolsError

logger = logging.getLogger(__name__)

app = typer.Typer(help="CLI Tool to manage financial assets", rich_markup_mode="rich")
console = Console()


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging output to the console."),
    json: bool = typer.Option(False, "--json", help="Format output in json format"),
    registry_filename: str = typer.Option(
        "static_assets.json", "--registry-filename", help="Path to the registry JSON file"
    ),
) -> None:
    """
    Bootstrap application and store CLI options in ctx.obj

    Executed before any subcommand.
    """

    # Ensure ctx.obj is initialized as a dictionary
    ctx.ensure_object(dict)

    # Choose the right adapters based on user flags
    # and build the services (+ configure logging)
    asset_service = bootstrap_app(verbose, registry_filename)

    # Save to the CLI context container
    ctx.obj["asset_service"] = asset_service

    # global CLI options to pass to every commands
    ctx.obj["JSON"] = json

    # access to the current command
    logger.debug(f"invoked command: {ctx.invoked_subcommand}")


@app.command()
def list_assets(
    ctx: typer.Context,
    name: Annotated[str | None, typer.Argument(help="must provide exact name")] = None,
    type: Annotated[str | None, typer.Argument(help="filter by asset type")] = None,
    market: Annotated[str | None, typer.Argument(help="filter by market")] = None,
) -> None:
    """
    Print by default the list of all [bold]assets[/bold] present in the [bold]identifier registry[/bold],
    static storage (file or DB)

    Use optional --name / --asset_type / --market to filter the output
    """

    logger.info("list_asset command with asset_type:%s and market:%s", type, market)

    # if a more configurable service factory was provided,
    # I could avoid to load yfinace_adapter everytime (if no web fetch required)
    asset_service = ctx.obj["asset_service"]

    assets: list[Asset] = []
    try:
        assets = asset_service.list_assets()
    except YFinanceToolsError as ex:
        rprint(f"[red]end program - {ex}[/red]")
        raise typer.Exit(code=1)

    if ctx.obj["JSON"]:
        # rprint([asset.to_dict() for asset in assets])
        rprint([asset.to_json() for asset in assets])
    else:
        title = f"Assets ([bold magenta]{len(assets)}[/bold magenta])"
        table = Table(title=title)
        table.add_column("Name", justify="right")
        table.add_column("Type", justify="center")
        table.add_column("ISIN", justify="center")
        table.add_column("yahoo_code", justify="left")

        for asset in assets:
            table.add_row(
                asset.name,
                asset.type.name,
                str(asset.isin) if asset.isin else "-",
                asset.yf_ticker or "-",
            )

        console.print(table)


@app.command()
def update_value(ctx: typer.Context, name: Annotated[str, typer.Argument(help="name of the asset")] = "Toto") -> None:
    """
    Retrieve last values of the asset from yahoo finance
    """
    logger.info("name:%s", name)
    rprint("[red]To implement[/red]")
    raise typer.Exit(1)


def main() -> None:
    """Entry point"""
    app()


# if __name__ == "__main__":
#     app()
