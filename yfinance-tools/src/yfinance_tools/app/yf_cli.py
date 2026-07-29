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
from yfinance_tools.domain import Asset, PendingIdentifierEntryUpdate, SelectorAssetBuilder
from yfinance_tools.domain.exceptions import YFinanceToolsError
from yfinance_tools.services.asset_service import AssetService

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="""CLI Tool to manage financial assets\n
    Global options for asset selection:
    Use --name and --type to filter assets (OR logic applied). For example:
    yfinance_cli --name AAPL --type FOREX list-assets
    """,
    rich_markup_mode="rich",
)
console = Console()


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging output to the console."),
    json: bool = typer.Option(False, "--json", help="Format output in json format"),
    registry_filename: str = typer.Option(
        "static_assets.json", "--registry-filename", help="Path to the registry JSON file"
    ),
    always_yes: bool = typer.Option(False, "--yes", help="do not ask for confirmation, always accept"),
    name: Annotated[str | None, typer.Option(help="must provide exact name")] = None,
    type: Annotated[str | None, typer.Option(help="filter by asset type")] = None,
    # market: Annotated[str | None, typer.Argument(help="filter by market")] = None,
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

    # create filter class
    selector = None
    # must hide, or YFinanceToolsError, must return None
    try:
        selector = SelectorAssetBuilder().with_name(name).with_type(type).build()
    except ValueError as ex:
        logger.error(str(ex))
        rprint(f"[red]end program - {ex}[/red]")
        raise typer.Exit(code=1)

    # Save to the CLI context container
    ctx.obj["asset_service"] = asset_service

    # global CLI options to pass to every commands
    ctx.obj["JSON"] = json
    ctx.obj["always_yes"] = always_yes
    ctx.obj["selector_asset"] = selector

    logger.debug("context settings:")
    logger.debug(f"JSON : {json}")
    logger.debug(f"always_yes : {always_yes}")
    logger.debug(f"selector_asset : {selector}")

    # access to the current command
    logger.debug(f"invoked command: {ctx.invoked_subcommand}")


@app.command()
def list_assets(
    ctx: typer.Context,
) -> None:
    """
    Print by default the list of all [bold]assets[/bold] present in the [bold]identifier registry[/bold],
    static storage (file or DB)

    Use optional --name / --asset_type / --market to filter the output
    """

    asset_service = ctx.obj["asset_service"]

    selector = ctx.obj["selector_asset"]
    logger.info(f"list_asset command with selector: {str(selector)}")
    logger.debug(f"debug selector: {selector} ")
    logger.debug(selector)

    assets: list[Asset] = []
    try:
        assets = asset_service.list_assets(selector=selector)
    except YFinanceToolsError as ex:
        rprint(f"[red]end program - {ex}[/red]")
        raise typer.Exit(code=1)

    print_assets(assets, ctx.obj["JSON"])


@app.command()
def update_static_data(
    ctx: typer.Context,
    force_all: Annotated[bool, typer.Option("--force-all", help="force fetching all assets")] = False,
) -> None:
    """
    Retrieve static identifers data from yahoo finance and update the registry
    """

    asset_service: AssetService = ctx.obj["asset_service"]

    selector = ctx.obj["selector_asset"]
    logger.info(f"update_static_data command with selector: {str(selector)}, force_all={force_all}")

    try:
        pendings: list[PendingIdentifierEntryUpdate] = asset_service.get_static_data_pending_update(selector, force_all)

    except YFinanceToolsError as ex:
        rprint(f"[red]end program - {ex}[/red]")
        raise typer.Exit(code=1)

    confirmed_pendings = []

    if ctx.obj["always_yes"]:
        confirmed_pendings = pendings
    else:
        for pending in pendings:
            rprint(pending)

            if typer.confirm(f"Do you want apply those changes for {pending.name} ?"):
                confirmed_pendings.append(pending)

    # update model and registry
    try:
        filepath, assets = asset_service.update_registry(confirmed_pendings)
    except YFinanceToolsError as ex:
        logger.error(str(ex))
        rprint(f"[red]end program - {ex}[/red]")
        raise typer.Exit(code=1)

    if len(assets) > 0:
        rprint(f"update done: {filepath}")
    else:
        rprint("nothing to update")
        return None

    print_assets(assets, ctx.obj["JSON"])


@app.command()
def update_value(ctx: typer.Context) -> None:
    """
    Retrieve last values of the asset from yahoo finance
    """
    logger.info("update_value")
    rprint("[red]To implement[/red]")
    raise typer.Exit(1)


#
# Helper methods
#


def print_assets(assets: list[Asset], json_output: bool) -> None:
    """Pretty print of assets"""

    if json_output:
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

    return None


def main() -> None:
    """Entry point"""
    app()
