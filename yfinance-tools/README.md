# CLI / TUI tools using yfinance

Purpose:
- create primary classes and services to use yfinance
- cli and tui tools to interact with the services
- unit and e2e tests for the code: double (mock) of yfinance
- validation tests: yfinance real use to assert network availability, data accessibility and report any break in yfinance and yahoo finance provider

## Packages

- Asset Management: store tickers of financial assets (yahoo_code, isin, names...)
- yfinance service: hide the use of yfinance and return data formatted for my use

## Installation - Dev

## Running Tools

```bash
uv sync
uv run yfinance_cli --help
# or in an active venv
yfinance_cli --help
```

## Running Tests

```bash
# added coverage configuration in pyproject.toml
uv run pytest
```

## Linter and formatter
```bash
# ruff configured in pyproject.toml
ruff check .
```

## Build Package
```bash
# build src and dist.whl packages in ./dist directory
uv build

# to "clean", delete all caches and *pyc files. to add in a Makefile if not better
find . -name ".venv" -prune -o -type d \( -name "__pycache__" -o -name ".pytest_cache" \) -print -exec rm -rf {} +
```

## VScode Settings


