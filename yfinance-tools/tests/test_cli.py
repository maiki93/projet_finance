"""
Test CLI tool

closer to integration/ e2e tests
- use bootstrap.py with real mplementation, generate debug.log
- still isolation of unit-testing, temprary directory / file for each test

Maybe later:
Split command / view UT
"""

import logging

import pytest
from typer.testing import CliRunner

import tests.utils as utils
from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.app.yf_cli import app

runner = CliRunner()


# apply to all tests in this file
# seems best approach, it is thoses tests which mess-up the logging
@pytest.fixture(autouse=True)
def deep_clean_logging_teardown():
    # Let the CLI bootstrap and test run normally
    yield

    # --- POST-TEST CLEANUP: Executed immediately after each test in this file ---

    # 1. Reset the Root Logger back to Python defaults
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.disabled = False

    # 2. Reset all named loggers (your logging.getLogger(__name__) instances)
    # We use list() because the dict might change size if threads are active
    for logger_name, logger_obj in list(root_logger.manager.loggerDict.items()):
        if isinstance(logger_obj, logging.Logger):
            # Reset to NOTSET so it falls back to inheriting from the root
            logger_obj.setLevel(logging.NOTSET)

            # CRITICAL: Re-enable propagation so caplog can see it again!
            logger_obj.propagate = True
            logger_obj.disabled = False

            # Strip out any custom handlers added by the CLI bootstrap
            for handler in logger_obj.handlers[:]:
                logger_obj.removeHandler(handler)


def test_cli_help() -> None:

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    # fixed content of help message
    assert "CLI Tool" in result.stdout


def test_cli_option_registry_filename(tmp_path, template_registry_data) -> None:

    registry_file = utils.create_file_with_content(tmp_path, "registry.json", template_registry_data)
    result = runner.invoke(app, ["--registry-filename", str(registry_file), "list-assets"])

    assert result.exit_code == 0
    assert f"Assets ({NB_ITEMS_TEMPLATE_REGISTRY_DATA})" in result.stdout


def test_cli_option_registry_not_existing_filename(tmp_path) -> None:

    not_existing_file = tmp_path / "toto.json"

    result = runner.invoke(app, ["--registry-filename", str(not_existing_file), "list-assets"])

    assert result.exit_code == 1
    assert "file not existing" in result.stdout


def test_cli_option_registry_not_valid_json(tmp_path) -> None:

    invalid_data = "garbage json content"
    invalid_registry_file = utils.create_file_with_content(tmp_path, "registry.json", invalid_data)

    result = runner.invoke(app, ["--registry-filename", str(invalid_registry_file), "list-assets"])

    assert result.exit_code == 1
    assert "Invalid JSON format" in result.stdout


def test_list_assets(tmp_path, template_registry_data) -> None:

    registry_file = utils.create_file_with_content(tmp_path, "registry.json", template_registry_data)

    result = runner.invoke(app, ["--registry-filename", str(registry_file), "list-assets"])

    assert result.exit_code == 0
    assert f"Assets ({NB_ITEMS_TEMPLATE_REGISTRY_DATA})" in result.stdout


def test_list_assets_json(tmp_path, template_registry_data) -> None:

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


@pytest.mark.webreq
def test_update_static_data(tmp_path, template_registry_data) -> None:
    registry_file = utils.create_file_with_content(tmp_path, "registry.json", template_registry_data)

    # Simulate user typing 'Y' and pressing Enter
    user_confirmation = "y\n" * NB_ITEMS_TEMPLATE_REGISTRY_DATA
    result = runner.invoke(
        app, ["--json", "--registry-filename", str(registry_file), "update-static-data"], input=user_confirmation
    )

    assert result.exit_code == 0
    # assert "update done, file is saved: (PosixPath('static_assets.json')" in result.stdout
    assert "update done:" in result.stdout


def test_update_value() -> None:

    result = runner.invoke(app, ["update-value"])

    assert result.exit_code == 1
    assert "To implement" in result.stdout
