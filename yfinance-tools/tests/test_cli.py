import json
from pathlib import Path

from typer.testing import CliRunner

from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.app.yf_cli import app

runner = CliRunner()

# default registry filename used in the cli tool
# avoid to pass --registry-filename option in all tests
DEFAULT_REGISTRY_FILENAME: str = "static_assets.json"


def _create_registry_file(tmp_path: Path, data: dict, filename: str = DEFAULT_REGISTRY_FILENAME):
    registry_file = tmp_path / filename
    with open(registry_file, "w") as f:
        json.dump(data, f)
    return registry_file


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # content of help message
    assert "CLI Tool" in result.stdout


def test_cli_option_registry_filename(tmp_path, template_registry_data):
    registry_file = _create_registry_file(tmp_path, template_registry_data)

    result = runner.invoke(app, ["--registry-filename", str(registry_file), "list-assets"])
    assert result.exit_code == 0
    assert f"Assets ({NB_ITEMS_TEMPLATE_REGISTRY_DATA})" in result.stdout


def test_cli_option_registry_not_existing_filename(tmp_path):
    not_existing_file = tmp_path / "toto.json"

    result = runner.invoke(app, ["--registry-filename", str(not_existing_file), "list-assets"])
    assert result.exit_code == 1
    assert "file not existing" in result.stdout


def test_cli_option_registry_not_valid_json(tmp_path):
    invalid_registry_file = tmp_path / "toto.json"

    with open(invalid_registry_file, "w") as f:
        f.write("garbage json content")

    result = runner.invoke(app, ["--registry-filename", str(invalid_registry_file), "list-assets"])
    assert result.exit_code == 1
    assert "invalid JSON format" in result.stdout


def test_list_assets(tmp_path, template_registry_data):
    registry_file = _create_registry_file(tmp_path, template_registry_data)

    result = runner.invoke(app, ["--registry-filename", str(registry_file), "list-assets"])
    assert result.exit_code == 0
    assert f"Assets ({NB_ITEMS_TEMPLATE_REGISTRY_DATA})" in result.stdout


def test_list_assets_json(tmp_path, template_registry_data):
    _create_registry_file(tmp_path, template_registry_data)

    result = runner.invoke(app, ["--json", "list-assets"])
    assert result.exit_code == 0
    assert "<yfinance_tools" in result.stdout


def test_verbose_in_stderr():
    result = runner.invoke(app, ["-v", "list-assets"])
    assert result.exit_code == 0
    assert "yfinance_tools - INFO - yfinance-tools.version" in result.stderr


def test_update_value():
    result = runner.invoke(app, ["update-value"])
    assert result.exit_code == 1
    assert "To implement" in result.stdout
