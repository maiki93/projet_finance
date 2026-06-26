"""
Test CLI tool

closer to integration/ e2e tests
- use bootstrap.py with real mplementation, generate debug.log
- still isolation of unit-testing, temprary directory / file for each test

Maybe later:
Split command / view UT
"""

from typer.testing import CliRunner

import tests.utils as utils
from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.app.yf_cli import app

runner = CliRunner()


def test_cli_help():

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    # fixed content of help message
    assert "CLI Tool" in result.stdout


def test_cli_option_registry_filename(tmp_path, template_registry_data):

    registry_file = utils.create_file_with_content(tmp_path, "registry.json", template_registry_data)
    result = runner.invoke(app, ["--registry-filename", str(registry_file), "list-assets"])

    assert result.exit_code == 0
    assert f"Assets ({NB_ITEMS_TEMPLATE_REGISTRY_DATA})" in result.stdout


def test_cli_option_registry_not_existing_filename(tmp_path):

    not_existing_file = tmp_path / "toto.json"

    result = runner.invoke(app, ["--registry-filename", str(not_existing_file), "list-assets"])

    assert result.exit_code == 1
    assert "file not existing" in result.stdout


def test_cli_option_registry_not_valid_json(tmp_path):

    invalid_data = "garbage json content"
    invalid_registry_file = utils.create_file_with_content(tmp_path, "registry.json", invalid_data)

    result = runner.invoke(app, ["--registry-filename", str(invalid_registry_file), "list-assets"])

    assert result.exit_code == 1
    assert "invalid JSON format" in result.stdout


def test_list_assets(tmp_path, template_registry_data):

    registry_file = utils.create_file_with_content(tmp_path, "registry.json", template_registry_data)

    result = runner.invoke(app, ["--registry-filename", str(registry_file), "list-assets"])

    assert result.exit_code == 0
    assert f"Assets ({NB_ITEMS_TEMPLATE_REGISTRY_DATA})" in result.stdout


def test_list_assets_json(tmp_path, template_registry_data):

    registry_file = utils.create_file_with_content(tmp_path, "registry.json", template_registry_data)

    result = runner.invoke(app, ["--json", "--registry-filename", str(registry_file), "list-assets"])

    assert result.exit_code == 0
    # Verify Rich-formatted output contains expected asset data and fields
    assert "name" in result.stdout
    assert "type" in result.stdout
    assert "isin" in result.stdout
    assert "yf_ticker" in result.stdout
    assert "quantum" in result.stdout
    assert len(result.stdout) > 0


def test_verbose_in_stderr(tmp_path, template_registry_data) -> None:

    registry_file = utils.create_file_with_content(tmp_path, "registry.json", template_registry_data)

    result = runner.invoke(app, ["-v", "--registry-filename", str(registry_file), "list-assets"])

    assert result.exit_code == 0
    assert "yfinance_tools - INFO - yfinance-tools.version" in result.stderr


def test_update_value():

    result = runner.invoke(app, ["update-value"])

    assert result.exit_code == 1
    assert "To implement" in result.stdout
