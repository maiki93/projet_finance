"""
Load and save asset identifiers in file (JSON format)
"""

import json
import pathlib

import pytest

from yfinance_tools.adapters.identifier_registry import InFileIdentifierRegistry
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError


def test_load_identifier_from_file(tmp_path: pathlib.Path, template_registry_data: dict):
    # create a valid temporary json file with the template data
    json_file = tmp_path / "static_ids.json"

    with open(json_file, "w") as f:
        json.dump(template_registry_data, f)

    # initialize registry
    registry = InFileIdentifierRegistry(str(json_file))

    # load data
    data_read = registry.load()
    assert len(data_read) == len(template_registry_data)


def test_load_invalid_json_file(tmp_path: pathlib.Path):
    # create an invalid json
    json_file = tmp_path / "invalid.json"

    with open(json_file, "w") as f:
        f.write("{]")

    # initialize registry
    registry = InFileIdentifierRegistry(str(json_file))

    with pytest.raises(IdentifierRegistryError):
        registry.load()


def test_load_file_donot_exist(tmp_path: pathlib.Path):
    # do not create file
    registry = InFileIdentifierRegistry(str(tmp_path / "static_ids.json"))

    with pytest.raises(IdentifierRegistryFileNotExistingError) as excinfo:
        registry.load()
    # file path is reported in error message
    assert "static_ids.json" in str(excinfo)
