# AI Agent Instructions: yfinance-tools

This document guides AI coding agents to be immediately productive in the yfinance-tools codebase. See the [README](README.md) for user-facing documentation.

## 🏗️ Architecture Overview

**yfinance-tools** uses **Hexagonal Architecture (DDD)** with four layers:

- **Domain** (`domain/`): Pure business logic. `Asset` (value object), `AssetType` (enum), `FinancialIdentifier` (data container)
- **Services** (`services/`): Orchestration logic. `AssetService` is stateless and depends only on **Protocol interfaces** (inversion of control)
- **Adapters** (`adapters/`): Concrete implementations. E.g., `InFileIdentifierRegistry` loads JSON from disk
- **App** (`app/`): CLI/TUI entry points. Typer-based CLI with dependency injection via context objects

This design enables:
- **Testability**: Swap implementations via Protocol-based dependency injection
- **Modularity**: Each layer has clear responsibilities
- **Extensibility**: Add new adapters without modifying services

## 🎯 Quick Start: Common Tasks

### Adding a New CLI Command
1. Open [app/yf_cli.py](src/yfinance_tools/app/yf_cli.py)
2. Define command using `@app.command()` decorator
3. **Use kebab-case names**: `@app.command("list-assets")` becomes `yfinance_cli list-assets`
4. Access injected `AssetService` via `ctx.obj["asset_service"]`
5. Return data as Rich table (default) or JSON if `--json` flag used
6. Errors: raise with red text via Rich console, exit code = 1

### Adding a New Service Method
1. Create method in `services` directory, e.g. [services/asset_service.py](src/yfinance_tools/services/asset_service.py)
2. **Only depend on Protocol interfaces**, not concrete classes (see [outbound_ports.py](src/yfinance_tools/services/outbound_ports.py))
3. Add corresponding test in tests, e.g. [tests/test_asset_service.py](tests/test_asset_service.py) using `asset_service_factory` fixture
4. If a new port is needed, add Protocol to [outbound_ports.py](src/yfinance_tools/services/outbound_ports.py)

### Adding a New Adapter (e.g., Database Registry)
1. Create new adapter in `adapters/` (e.g., `postgres_identifier_registry.py`)
2. **Implement the Protocol** from [outbound_ports.py](src/yfinance_tools/services/outbound_ports.py)
3. Create fake for tests in `tests/fakes/` (e.g., `FakePostgresRegistry`)
4. Update [bootstrap.py](src/yfinance_tools/bootstrap.py) to wire the adapter into `AssetService`
5. Update CLI tests to use new fake if adapter is used

## 📋 Naming Conventions

| Category | Pattern | Example |
|----------|---------|---------|
| **Files/Folders** | `snake_case` | `asset_service.py`, `identifier_registry.py` |
| **Classes** | `PascalCase` | `AssetService`, `InFileIdentifierRegistry` |
| **Private members** | `_snake_case` | `_registry`, `_logger` |
| **Constants** | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT` |
| **CLI commands** | `kebab-case` | `list-assets` (not `list_assets`) |
| **Test functions** | `test_*` | `test_asset_creation_with_valid_data()` |
| **Test fakes** | `Fake{Interface}` | `FakeIdentifierRegistry` |

## 🧪 Testing Strategy

- **Fixtures** ([conftest.py](tests/conftest.py)): Reusable `asset_service_factory`, `template_registry_data` (5 diverse assets)
- **Fakes** ([fakes/](tests/fakes/)): Implement Protocols to avoid I/O in unit tests. Do not use mocks if possible; implement the Protocol interface.
- **No real network calls**: All yfinance usage must be faked/mocked in tests
- **CLI testing**: Use `CliRunner` from Typer to invoke commands in isolation
- **Coverage requirement**: 90% minimum (branch coverage enabled via pytest config)

### Example: Testing a New Service Method
```python
def test_new_method_returns_valid_data(asset_service_factory):
    service = asset_service_factory()
    result = service.new_method()
    assert result is not None
    assert len(result) > 0  # Adjust based on method logic
```

## 🔧 Development Workflow

### Install & Setup

Install all dependencies (dev + production)
```bash
uv sync
```

### Run Tests

Run all or a specific test, generate HTML coverage report (configuration in `pyproject.toml`)
```bash
uv run pytest
uv run pytest tests/test_asset_service.py::test_specific_function
```

### Linting & Code Quality

Check for style issues, correct formatting (Auto-formatting is configured in `pyproject.toml`).
```bash
uv run ruff check .
uv run ruff format file.py
```

### Build & Package
```bash
uv build             # Build wheel and src.tar.gz in ./dist/
```

### Test CLI Locally
```bash
uv run yfinance_cli --help              # Show all commands
uv run yfinance_cli list-assets         # Run command
uv run yfinance_cli list-assets --type EQUITY  # Run command with argument
uv run yfinance_cli --json list-assets  # JSON output (CLI optional ouput)
uv run yfinance_cli -v list-assets      # Verbose logging (CLI optional output)
```

## 🚀 Dependency Injection & Bootstrap

The app uses **Protocol-based dependency injection** to enable testing and extensibility:

1. **[bootstrap.py](src/yfinance_tools/bootstrap.py)** wires the application on startup
2. **Logging** is configured from `config/logging_config.yaml`
3. **Registry adapter** is instantiated with `static_assets.json`
4. **AssetService** is created with the registry
5. All of this is passed to the CLI via the Typer context (`ctx.obj`)

**Example: How the CLI accesses services**
```python
@app.callback()
def setup(ctx: typer.Context):
    ctx.obj = bootstrap_app()  # Returns dict with all services

@app.command()
def list_assets(ctx: typer.Context):
    service = ctx.obj["asset_service"]  # Retrieve injected service
    return service.get_all_assets()
```

## ⚠️ Common Pitfalls & Best Practices

1. **Don't hardcode file paths** → Use adapters (Protocols) instead; keeps code testable
2. **CLI command names in kebab-case** → `@app.command("my-command")`, not snake_case
3. **Test fakes must implement Protocols exactly** → Mypy will catch mismatches if using strict mode
4. **Always pass services via context** → Don't create singletons or global state in CLI
5. **Maintain 90% coverage** → CI checks this; new code must include tests
6. **Asset modifications require JSON + test updates** → Keep `static_assets.json` and fixtures in sync

## 📦 Key Dependencies

- **yfinance** (1.4.1+) — Financial data provider (integration in progress)
- **typer** (0.26.7+) — Type-safe CLI framework
- **textual** (8.2.7+) — TUI framework (yf_tui.py exists but unimplemented)
- **pyyaml** — YAML config parsing
- **pytest** (9.0.3+), **pytest-cov** — Testing & coverage
- **ruff** (0.15.17+) — Linting & formatting

## 📁 Folder Guide

| Folder | Purpose |
|--------|---------|
| `src/yfinance_tools/domain/` | Business logic (value objects, enums) |
| `src/yfinance_tools/services/` | Orchestration & Protocol definitions |
| `src/yfinance_tools/adapters/` | Concrete implementations of Protocols |
| `src/yfinance_tools/app/` | CLI/TUI entry points (Typer, Textual) |
| `src/yfinance_tools/config/` | Configuration files (logging YAML) |
| `tests/` | Unit & integration tests |
| `tests/fakes/` | Test double implementations of Protocols |
| `static_assets.json` | Financial asset registry (5 core assets) |
| `htmlcov/` | Code coverage report (generated by pytest) |

---

**Last updated**: 2026-06-24
**For questions about project structure**: See [README](README.md) or individual module docstrings
