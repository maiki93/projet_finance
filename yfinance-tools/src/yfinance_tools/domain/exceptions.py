class YFinanceToolsError(Exception):
    """Base exception for the whole application."""

    pass


class IdentifierRegistryError(YFinanceToolsError):
    """Errors related to the loading or format of financial identifiers."""

    pass


class IdentifierRegistryFileNotExistingError(YFinanceToolsError):
    """Errors related to the loading or format of financial identifiers."""

    pass
