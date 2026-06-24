"""
Application boostrapping:
- configure logging
- load default outbound adapters to create AssetService
"""

import logging
import logging.config
from importlib import resources

import yaml

import yfinance_tools  # only for accessing __version__
from yfinance_tools.adapters import InFileIdentifierRegistry
from yfinance_tools.services import AssetService


def bootstrap_app(verbose: bool = False, registry_filename: str = "static_assets.json") -> AssetService:
    """Initializes configuration, logging, and wires dependencies."""

    # reads the file directly from the package structure
    # TODO outsource package, /config, filename -< some cli arguments
    config_file = resources.files("yfinance_tools.config").joinpath("logging_config.yaml")
    with config_file.open("r") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)

    yfinance_logger = logging.getLogger(yfinance_tools.__name__)

    # global verbose mode, apply to root logger
    # - debug messages of external libraries
    # - debug messages of yfinance-tools
    # - test: add the console handler => every output both in file and in console
    if verbose:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        # Ensure all existing handlers (like console stdout) also accept DEBUG logs
        for handler in root_logger.handlers:
            handler.setLevel(logging.DEBUG)

        # test: in this mode all logs are also sent to the console
        console_handler = logging.getHandlerByName("console")
        if console_handler and console_handler not in yfinance_logger.handlers:
            yfinance_logger.addHandler(console_handler)
            root_logger.addHandler(console_handler)

        # Set this library and all handlers to DEBUG
        yfinance_logger.setLevel(logging.DEBUG)
        for handler in yfinance_logger.handlers:
            handler.setLevel(logging.DEBUG)

    yfinance_logger.info(f"yfinance-tools.version: {yfinance_tools.__version__}")
    yfinance_logger.info(f"globally enabled debug: {verbose}")

    # use provided registry filename or default
    asset_service = AssetService(InFileIdentifierRegistry(registry_filename), None)
    return asset_service
