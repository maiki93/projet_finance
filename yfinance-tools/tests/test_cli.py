# tests/test_cli.py
from typer.testing import CliRunner

from yfinance_tools.app.yf_cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "CLI Tool" in result.stdout


def test_list_assets():
    result = runner.invoke(app, ["list-assets"])
    assert result.exit_code == 0
    assert "Assets (5)" in result.stdout


def test_list_assets_json():
    result = runner.invoke(app, ["--json", "list-assets"])
    assert result.exit_code == 0
    assert "<yfinance_tools" in result.stdout


def test_verbose_in_stderr():
    result = runner.invoke(app, ["-v", "list-assets"])
    assert result.exit_code == 0
    assert "yfinance_tools - INFO - yfinance-tools.version" in result.stderr


# need argument
# def test_missing_asset_json():
#    result = runner.invoke(app, ["-v", "list-assets"])
#    assert result.exit_code == 0


def test_update_value():
    result = runner.invoke(app, ["update-value"])
    assert result.exit_code == 1
    assert "To implement" in result.stdout
